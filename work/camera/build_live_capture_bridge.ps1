param([string]$OutputDir,[string]$ObjectDir='',[string]$CompilerBin='C:\msys64\mingw64\bin')
$ErrorActionPreference='Stop'
if(!$OutputDir){throw 'Supply the isolated live-window build directory as -OutputDir.'}
$OutputDir=[IO.Path]::GetFullPath($OutputDir)
if(!$ObjectDir){$ObjectDir=Join-Path $OutputDir 'objects'}
$project=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$package=Join-Path $project 'work\v2\package\NFSUG-Native-Renderer-source'
$gcc=Join-Path $CompilerBin 'gcc.exe'
$archive=Join-Path $package 'build\mgba-nfsug\libmgba.a'
foreach($path in @($gcc,$archive,$ObjectDir)){if(!(Test-Path -LiteralPath $path)){throw "Missing build input: $path"}}
$env:PATH=$CompilerBin+';'+$env:PATH
[IO.Directory]::CreateDirectory($OutputDir)|Out-Null
$flags=@('-O2','-ffunction-sections','-fdata-sections','-DBUILD_STATIC','-DM_CORE_GBA','-DUSE_DEBUGGERS','-DNF_VISIBILITY_CAPTURE','-DNF_ROAD_ATTRIBUTE_CORRECTION','-DNF_PROBE_EXPORTS','-D_GNU_SOURCE','-D_WIN32_WINNT=0x0600',('-I'+(Join-Path $package 'deps\mgba-0.10.5\include')),('-I'+(Join-Path $package 'build\mgba-nfsug\include')),('-I'+(Join-Path $project 'work')))
function Cache-BridgeInputs([string]$DependencyFile,[string]$ProjectRoot,[string]$CacheRoot){
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
 @{created_at=[DateTime]::Now.ToString('o');inputs=$manifest}|ConvertTo-Json -Depth 4|Set-Content -LiteralPath (Join-Path $CacheRoot 'bridge-cache.json') -Encoding UTF8
 return $CacheRoot
}

$cacheRoot=Join-Path $OutputDir "bridge-input-cache"
$object=Join-Path $ObjectDir 'live_capture_bridge.o'
$compileFlags=$flags;$compileSource=Join-Path $project 'work\probe.c'
$cached=Cache-BridgeInputs (Join-Path $ObjectDir 'live_capture_bridge.d') $project $cacheRoot
if($cached){
 $compileFlags=@($flags|ForEach-Object {$_.Replace($project,$cacheRoot)})
 $compileSource=$compileSource.Replace($project,$cacheRoot)
 foreach($include in @((Join-Path $project 'work'),(Join-Path $project 'work\camera'),(Join-Path $package 'deps\mgba-0.10.5\include'),(Join-Path $package 'build\mgba-nfsug\include'))){$compileFlags+=@('-idirafter',$include)}
 Write-Output 'Using refreshed local bridge input cache.'
}
& $gcc @compileFlags -c $compileSource -o $object -MMD
if($LASTEXITCODE){throw 'Live capture bridge compilation failed.'}
# Reuse the support objects produced by build_live_game_window.ps1.
$names=@(Get-Content -LiteralPath (Join-Path $package 'camera\native-renderer-sources.txt')|Where-Object {$_ -and !$_.StartsWith('#') -and $_ -notin @('packet_preview.c','scene_packet.c')}|ForEach-Object {[IO.Path]::GetFileNameWithoutExtension($_)})
$names+=@('scene_packet','scene_segments','candidate_packet','obj_tile')
$objects=@($object)
foreach($name in $names){
 $path=Join-Path $ObjectDir ($name+'.o')
 if(!(Test-Path -LiteralPath $path)){throw "Build the live-window support objects first; missing $path"}
 $objects+=@($path)
}
$dll=Join-Path $OutputDir 'nfsprobe-background-only.dll'
& $gcc -O2 -shared @flags (Join-Path $project 'outputs\nfsug-research\native_span.c') @objects $archive -lws2_32 -lshlwapi -lole32 -luuid '-Wl,--gc-sections' -lopengl32 -lgdi32 -lcomdlg32 -lwinmm -luser32 -o $dll
if($LASTEXITCODE){throw 'Live capture bridge link failed.'}
# Preserve compiler-listed source provenance alongside the isolated binary.
$sha=[Security.Cryptography.SHA256]::Create();$inputs=@()
try{
 foreach($line in Get-Content -LiteralPath (Join-Path $ObjectDir 'live_capture_bridge.d')){
  $path=$line.Trim()
  if($path.EndsWith(' \')){$path=$path.Substring(0,$path.Length-2).TrimEnd()}
  $path=$path.Replace('\ ',' ')
  if($path.StartsWith($cacheRoot+'\')){$path=$project+$path.Substring($cacheRoot.Length)}
  if($path.StartsWith($project+'\')){
   $data=[IO.File]::ReadAllBytes($path)
   $inputs+=@{path=$path;sha256=([BitConverter]::ToString($sha.ComputeHash($data))).Replace('-','')}
  }
 }
 $inputs+=@{path=(Join-Path $project 'outputs\nfsug-research\native_span.c');sha256=([BitConverter]::ToString($sha.ComputeHash([IO.File]::ReadAllBytes((Join-Path $project 'outputs\nfsug-research\native_span.c'))))).Replace('-','')}
 @{inputs=$inputs;flags=$flags;support_objects=$objects;dll_sha256=([BitConverter]::ToString($sha.ComputeHash([IO.File]::ReadAllBytes($dll)))).Replace('-','');scope='Isolated bridge; default full capture preserved. Support objects must come from a current live-window build.'}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $OutputDir 'live-capture-build.json') -Encoding UTF8
}finally{$sha.Dispose()}
Write-Output "Built isolated bridge: $dll"
