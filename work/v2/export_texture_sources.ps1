param(
    [Parameter(Mandatory = $true)][string]$Inventory,
    [Parameter(Mandatory = $true)][string]$Destination
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$drawingAssembly = [System.Drawing.Bitmap].Assembly
$references = [Collections.Generic.List[string]]::new()
$references.Add($drawingAssembly.Location)
foreach ($reference in $drawingAssembly.GetReferencedAssemblies()) {
    try {
        $loaded = [Reflection.Assembly]::Load($reference)
        if ($loaded.Location) { $references.Add($loaded.Location) }
    } catch { }
}
$references = @($references | Select-Object -Unique)

Add-Type -ReferencedAssemblies $references -TypeDefinition @'
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;

public static class NfTexturePngExporter {
    public static string SourceHash(byte[] rgba, int width, int height) {
        unchecked {
            ulong value = 14695981039346656037UL;
            uint w = (uint)width, h = (uint)height;
            for (int i = 0; i < 4; i++) value = (value ^ (byte)(w >> (i * 8))) * 1099511628211UL;
            for (int i = 0; i < 4; i++) value = (value ^ (byte)(h >> (i * 8))) * 1099511628211UL;
            foreach (byte b in rgba) value = (value ^ b) * 1099511628211UL;
            return value.ToString("x16");
        }
    }

    public static void SaveAndVerify(byte[] rgba, int width, int height, string path) {
        using (Bitmap bitmap = new Bitmap(width, height, PixelFormat.Format32bppArgb)) {
            for (int y = 0; y < height; y++) {
                for (int x = 0; x < width; x++) {
                    int i = (y * width + x) * 4;
                    bitmap.SetPixel(x, y, Color.FromArgb(rgba[i + 3], rgba[i], rgba[i + 1], rgba[i + 2]));
                }
            }
            bitmap.Save(path, ImageFormat.Png);
        }
        using (Bitmap decoded = new Bitmap(path)) {
            if (decoded.Width != width || decoded.Height != height)
                throw new InvalidOperationException("PNG dimensions changed during encoding");
            for (int y = 0; y < height; y++) {
                for (int x = 0; x < width; x++) {
                    int i = (y * width + x) * 4;
                    Color c = decoded.GetPixel(x, y);
                    if (c.R != rgba[i] || c.G != rgba[i + 1] || c.B != rgba[i + 2] || c.A != rgba[i + 3])
                        throw new InvalidOperationException("PNG pixel or alpha mismatch");
                }
            }
        }
    }
}
'@

$inventoryPath = [IO.Path]::GetFullPath($Inventory)
$destinationPath = [IO.Path]::GetFullPath($Destination)
$rowsPath = Join-Path $inventoryPath 'source-inventory.tsv'
if (-not (Test-Path -LiteralPath $rowsPath -PathType Leaf)) { throw "Missing inventory: $rowsPath" }
if (Test-Path -LiteralPath $destinationPath) { throw "Refusing to overwrite: $destinationPath" }
$parent = Split-Path -Parent $destinationPath
New-Item -ItemType Directory -Path $parent -Force | Out-Null
$stage = Join-Path $parent ((Split-Path -Leaf $destinationPath) + '.building-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $stage | Out-Null

try {
    $entries = [Collections.Generic.List[object]]::new()
    $seen = @{}
    [long]$totalBytes = 0
    $lineNumber = 0
    foreach ($line in [IO.File]::ReadAllLines($rowsPath, [Text.Encoding]::ASCII)) {
        $lineNumber++
        $fields = $line.Split("`t")
        if ($fields.Length -notin 5, 7, 9) { throw "Malformed inventory row $lineNumber" }
        $key = $fields[0].ToLowerInvariant()
        if ($key -notmatch '^[0-9a-f]{16}$') { throw "Invalid texture key at row $lineNumber" }
        $width = [int]$fields[1]; $height = [int]$fields[2]
        if ($width -le 0 -or $height -le 0 -or ([long]$width * $height) -gt (4096L * 4096L)) {
            throw "Invalid texture dimensions at row $lineNumber"
        }
        $blobPath = Join-Path $inventoryPath ($key + '.rgba')
        $rgba = [IO.File]::ReadAllBytes($blobPath)
        if ($rgba.LongLength -ne ([long]$width * $height * 4)) { throw "RGBA size mismatch at row $lineNumber" }
        if ([NfTexturePngExporter]::SourceHash($rgba, $width, $height) -ne $key) { throw "Source hash mismatch at row $lineNumber" }
        if ($seen.ContainsKey($key)) {
            if ($seen[$key].width -ne $width -or $seen[$key].height -ne $height) { throw "Conflicting dimensions for $key" }
            continue
        }

        $name = $key + '.png'
        [NfTexturePngExporter]::SaveAndVerify($rgba, $width, $height, (Join-Path $stage $name))
        $entry = [ordered]@{ hash = $key; width = $width; height = $height; address = [Convert]::ToUInt32($fields[3], 16); kind = [int]$fields[4]; source = $name }
        if ($fields.Length -eq 7) {
            $entry.first_seen_process_id = [uint32]$fields[5]
            $entry.first_seen_draw_serial = [uint32]$fields[6]
        } elseif ($fields.Length -eq 9) {
            $entry.stride = [uint32]$fields[5]
            $entry.shade = [uint32]$fields[6]
            $entry.first_seen_process_id = [uint32]$fields[7]
            $entry.first_seen_draw_serial = [uint32]$fields[8]
        }
        $seen[$key] = $entry
        $entries.Add([pscustomobject]$entry)
        $totalBytes += $rgba.LongLength
    }

    $manifest = [ordered]@{
        format = 'NFSUG-SOURCE-TEXTURE-INVENTORY-1'
        complete = $false
        coverage = 'captured only from the ROM states and frames exercised'
        texture_count = $entries.Count
        source_rgba_bytes = $totalBytes
        textures = @($entries)
    }
    $json = $manifest | ConvertTo-Json -Depth 8
    [IO.File]::WriteAllText((Join-Path $stage 'inventory.json'), $json, [Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $stage -Destination $destinationPath
    [pscustomobject]@{ format = $manifest.format; complete = $false; texture_count = $entries.Count; source_rgba_bytes = $totalBytes; destination = $destinationPath } | ConvertTo-Json
} catch {
    # Preserve the incomplete staging folder for inspection; never remove user data here.
    throw
}
