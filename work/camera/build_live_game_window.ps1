param([string]$OutputDir='', [string]$CompilerBin='C:\msys64\mingw64\bin', [switch]$HarnessOnly,[switch]$LinkOnly)
$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
if(!$OutputDir){$OutputDir=Join-Path $env:TEMP 'NFSUG-live-window-build'}
$OutputDir=[IO.Path]::GetFullPath($OutputDir)
$package=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\v2\package\NFSUG-Native-Renderer-source'))
$gcc=Join-Path $CompilerBin 'gcc.exe'
$archive=Join-Path $package 'build\mgba-nfsug\libmgba.a'
foreach($path in @($gcc,$archive)){if(!(Test-Path -LiteralPath $path)){throw "Missing build dependency: $path"}}
$env:PATH=$CompilerBin+';'+$env:PATH
New-Item -ItemType Directory -Force $OutputDir | Out-Null
$objectDir=Join-Path $OutputDir 'objects';New-Item -ItemType Directory -Force $objectDir|Out-Null
$flags=@(('-B'+$CompilerBin.Replace('\','/')+'/'),'-O2','-ffunction-sections','-fdata-sections','-DBUILD_STATIC','-DM_CORE_GBA','-DUSE_DEBUGGERS','-DNF_VISIBILITY_CAPTURE','-DNF_ROAD_ATTRIBUTE_CORRECTION','-D_GNU_SOURCE','-D_WIN32_WINNT=0x0600',('-I'+(Join-Path $package 'deps\mgba-0.10.5\include')),('-I'+(Join-Path $package 'build\mgba-nfsug\include')),('-I'+$PSScriptRoot),('-I'+(Join-Path $package 'camera')),('-I'+(Join-Path $package 'v2')),('-I'+$package))
$sources=@((Join-Path $PSScriptRoot 'live_game_window.c'))
$sources+=@(Get-Content (Join-Path $package 'camera\native-renderer-sources.txt')|Where-Object {$_ -and !($_.StartsWith('#')) -and $_ -ne 'packet_preview.c' -and $_ -ne 'scene_packet.c'}|ForEach-Object {Join-Path (Join-Path $package 'camera') $_})
$sources+=@((Join-Path $PSScriptRoot 'scene_packet.c'),(Join-Path $PSScriptRoot 'scene_segments.c'),(Join-Path $PSScriptRoot 'candidate_packet.c'),(Join-Path $PSScriptRoot 'obj_tile.c'))
function Cache-HarnessInputs([string]$DependencyFile,[string]$ProjectRoot,[string]$CacheRoot){
 if(!(Test-Path -LiteralPath $DependencyFile)){return $null}
 $paths=@(Get-Content -LiteralPath $DependencyFile|ForEach-Object {
  $p=$_.Trim();if($p.EndsWith(' \')){$p=$p.Substring(0,$p.Length-2).TrimEnd()};$p=$p.Replace('\ ',' ')
  if($p.StartsWith($CacheRoot+'\')){$p=$ProjectRoot+$p.Substring($CacheRoot.Length)}
  if($p.StartsWith($ProjectRoot+'\')){$p}
 }|Select-Object -Unique)
 if(!$paths.Count){return $null}
 $manifest=@();$sha=[Security.Cryptography.SHA256]::Create()
 try{foreach($p in $paths){
  $destination=Join-Path $CacheRoot $p.Substring($ProjectRoot.Length+1)
  [IO.Directory]::CreateDirectory((Split-Path $destination -Parent))|Out-Null
  $data=[IO.File]::ReadAllBytes($p);[IO.File]::WriteAllBytes($destination,$data)
  $manifest+=@{source=$p;sha256=([BitConverter]::ToString($sha.ComputeHash($data))).Replace('-','').ToLowerInvariant()}
 }}finally{$sha.Dispose()}
 @{created_at=[DateTime]::Now.ToString('o');inputs=$manifest}|ConvertTo-Json -Depth 4|Set-Content -LiteralPath (Join-Path $CacheRoot 'harness-cache.json') -Encoding UTF8
 return $CacheRoot
}
$objects=@();$ordinal=0
foreach($source in $sources){
 $object=Join-Path $objectDir (([IO.Path]::GetFileNameWithoutExtension($source))+'.o');$objects+=@($object);$ordinal++
 # Reuse support objects only when their source/shared headers are unchanged.
 if($LinkOnly -or ($HarnessOnly -and $ordinal -gt 1)){if(!(Test-Path $object)){throw 'HarnessOnly needs a completed full build first.'};continue}
 Write-Output "compile $ordinal/$($sources.Count): $([IO.Path]::GetFileName($source))"
 $compileFlags=$flags;$compileSource=$source
 if($HarnessOnly -and $ordinal -eq 1){
  $projectRoot=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
  $cache=Cache-HarnessInputs (Join-Path $objectDir 'live_game_window.d') $projectRoot (Join-Path $OutputDir 'network-input-cache')
  if($cache){
   $compileFlags=@($flags|ForEach-Object {$_.Replace($projectRoot,$cache)})
   # New project includes remain resolvable; system headers avoid slow Y: probes.
   foreach($include in @($PSScriptRoot,(Join-Path $package 'camera'),(Join-Path $package 'v2'),$package,(Join-Path $package 'deps\mgba-0.10.5\include'),(Join-Path $package 'build\mgba-nfsug\include'))){$compileFlags+=@('-idirafter',$include)}
   $compileSource=$source.Replace($projectRoot,$cache)
   Write-Output 'Using refreshed local harness input cache.'
  }
 }
 $compileArgs=$compileFlags+@('-c',$compileSource,'-o',$object,'-MMD')
 & $gcc @compileArgs
 if($LASTEXITCODE){throw "Compilation failed for $source (exit $LASTEXITCODE)."}
}
$exe=Join-Path $OutputDir 'NFSUG-Live-Window-Test.exe'
$linkArgs=$objects+@($archive,'-lws2_32','-lshlwapi','-lole32','-luuid','-Wl,--gc-sections','-lopengl32','-lgdi32','-lcomdlg32','-lwinmm','-luser32','-mwindows','-o',$exe)
& $gcc @linkArgs
if($LASTEXITCODE){throw "Live window link failed (exit $LASTEXITCODE)."}
@{built_at=[DateTime]::Now.ToString('o');binary=$exe;source_count=$sources.Count;harness_only=[bool]$HarnessOnly;link_only=[bool]$LinkOnly;exit_code=0}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $OutputDir 'build-report.json') -Encoding UTF8
Write-Output "Built: $exe"