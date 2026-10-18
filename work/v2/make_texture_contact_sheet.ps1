param(
    [Parameter(Mandatory = $true)][string]$TextureDirectory,
    [Parameter(Mandatory = $true)][string]$Destination
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$source = [IO.Path]::GetFullPath($TextureDirectory)
$output = [IO.Path]::GetFullPath($Destination)
$manifestPath = Join-Path $source 'inventory.json'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { throw "Missing inventory manifest: $manifestPath" }
if (Test-Path -LiteralPath $output) { throw "Refusing to overwrite contact sheet: $output" }
$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$entries = @($manifest.textures)
if ($entries.Count -eq 0) { throw 'Texture inventory is empty.' }

$columns = 5; $cellWidth = 240; $cellHeight = 160
$rows = [int][Math]::Ceiling($entries.Count / [double]$columns)
$sheet = [Drawing.Bitmap]::new($columns * $cellWidth, $rows * $cellHeight, [Drawing.Imaging.PixelFormat]::Format24bppRgb)
$graphics = [Drawing.Graphics]::FromImage($sheet)
$graphics.Clear([Drawing.Color]::FromArgb(32, 35, 40))
$graphics.InterpolationMode = [Drawing.Drawing2D.InterpolationMode]::NearestNeighbor
$graphics.PixelOffsetMode = [Drawing.Drawing2D.PixelOffsetMode]::Half
$font = [Drawing.Font]::new('Segoe UI', 9, [Drawing.FontStyle]::Regular)
$brush = [Drawing.SolidBrush]::new([Drawing.Color]::White)
$line = [Drawing.Pen]::new([Drawing.Color]::FromArgb(90, 100, 110))
try {
    for ($i = 0; $i -lt $entries.Count; $i++) {
        $entry = $entries[$i]
        $path = Join-Path $source $entry.source
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing PNG: $path" }
        $image = [Drawing.Image]::FromFile($path)
        try {
            if ($image.Width -ne $entry.width -or $image.Height -ne $entry.height) { throw "Dimension mismatch: $path" }
            $x = ($i % $columns) * $cellWidth
            $y = [int][Math]::Floor($i / [double]$columns) * $cellHeight
            $scale = [Math]::Min(220.0 / $image.Width, 112.0 / $image.Height)
            $width = [Math]::Max(1, [int][Math]::Round($image.Width * $scale))
            $height = [Math]::Max(1, [int][Math]::Round($image.Height * $scale))
            $rect = [Drawing.Rectangle]::new($x + [int](($cellWidth - $width) / 2), $y + 4, $width, $height)
            $graphics.DrawImage($image, $rect)
            $graphics.DrawRectangle($line, $x + 1, $y + 1, $cellWidth - 3, $cellHeight - 3)
            $label = '{0}  {1}x{2}  kind {3}' -f $entry.hash.Substring(0, 8), $entry.width, $entry.height, $entry.kind
            $graphics.DrawString($label, $font, $brush, [single]($x + 7), [single]($y + 122))
        } finally { $image.Dispose() }
    }
    $parent = Split-Path -Parent $output
    if ($parent) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    $sheet.Save($output, [Drawing.Imaging.ImageFormat]::Png)
} finally {
    $line.Dispose(); $brush.Dispose(); $font.Dispose(); $graphics.Dispose(); $sheet.Dispose()
}
$check = [Drawing.Image]::FromFile($output)
try { if ($check.Width -ne ($columns * $cellWidth) -or $check.Height -ne ($rows * $cellHeight)) { throw 'Contact-sheet dimensions failed verification.' } }
finally { $check.Dispose() }
[pscustomobject]@{ textureCount = $entries.Count; columns = $columns; rows = $rows; width = $columns * $cellWidth; height = $rows * $cellHeight; destination = $output } | ConvertTo-Json
