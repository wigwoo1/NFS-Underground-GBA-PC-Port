param(
 [Parameter(Mandatory=$true)][string]$NdkRoot,
 [Parameter(Mandatory=$true)][string]$MgbaSource,
 [Parameter(Mandatory=$true)][string]$Ninja,
 [string]$OutputRoot='C:\NFSUG-Workspace\NFSUG-android-local',
 [string[]]$Abis=@('arm64-v8a','x86_64'),
 [int]$Api=26,[int]$Parallel=8,[switch]$Jni,
 [string]$CMake=(Get-Command cmake -ErrorAction Stop).Source
)
$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
$NdkRoot=[IO.Path]::GetFullPath($NdkRoot)
$MgbaSource=[IO.Path]::GetFullPath($MgbaSource)
$OutputRoot=[IO.Path]::GetFullPath($OutputRoot)
$toolchain=Join-Path $NdkRoot 'build\cmake\android.toolchain.cmake'
foreach($path in @($toolchain,(Join-Path $MgbaSource 'CMakeLists.txt'),$Ninja,$CMake)){
 if(!(Test-Path -LiteralPath $path)){throw "Missing Android build input: $path"}
}
if($Api -lt 26 -or $Api -gt 36 -or $Parallel -lt 1 -or $Parallel -gt 16){throw 'Use API 26..36 and 1..16 build workers.'}
[IO.Directory]::CreateDirectory($OutputRoot)|Out-Null
$project=Join-Path $OutputRoot 'core-project'
[IO.Directory]::CreateDirectory($project)|Out-Null
$sha=[Security.Cryptography.SHA256]::Create()
$inputs=@();$results=@()
try{
 foreach($name in @('CMakeLists.txt','nfsug_android_core.c','nfsug_android_core.h','nfsug_android_jni.c')){
  $data=[IO.File]::ReadAllBytes((Join-Path $PSScriptRoot $name))
  [IO.File]::WriteAllBytes((Join-Path $project $name),$data)
  $inputs+=@{name=$name;sha256=([BitConverter]::ToString($sha.ComputeHash($data))).Replace('-','')}
 }
 foreach($abi in $Abis){
  if($abi -notin @('arm64-v8a','x86_64')){throw "Unsupported initial Android ABI: $abi"}
  $dir=Join-Path $OutputRoot ('build-'+$abi)
  $configure=Join-Path $OutputRoot ('configure-'+$abi+'.log')
  $build=Join-Path $OutputRoot ('build-'+$abi+'.log')
  Write-Output "Configuring Android $abi / API $Api"
  & $CMake -S $project -B $dir -G Ninja "-DCMAKE_MAKE_PROGRAM=$Ninja" "-DCMAKE_TOOLCHAIN_FILE=$toolchain" "-DANDROID_ABI=$abi" "-DANDROID_PLATFORM=android-$Api" '-DCMAKE_BUILD_TYPE=Release' "-DNFSUG_MGBA_SOURCE=$MgbaSource" '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON' "-DNFSUG_ANDROID_JNI=$([int][bool]$Jni)" *> $configure
  if($LASTEXITCODE){Get-Content -LiteralPath $configure -Tail 18;throw "Android $abi configuration failed; see $configure"}
  Write-Output "Building Android $abi core library"
  & $CMake --build $dir --target nfsug_android_core --parallel $Parallel *> $build
  if($LASTEXITCODE){Get-Content -LiteralPath $build -Tail 28;throw "Android $abi compilation failed; see $build"}
  $library=Join-Path $dir 'libnfsug_android_core.so'
  $bytes=[IO.File]::ReadAllBytes($library)
  $machine=[BitConverter]::ToUInt16($bytes,18)
  $expected=if($abi -eq 'arm64-v8a'){183}else{62}
  if($bytes[0] -ne 127 -or $bytes[1] -ne 69 -or $bytes[2] -ne 76 -or $bytes[3] -ne 70 -or $bytes[4] -ne 2 -or $bytes[5] -ne 1 -or [BitConverter]::ToUInt16($bytes,16) -ne 3 -or $machine -ne $expected){throw "Wrong ELF target for $abi"}
  $readelf=Join-Path $NdkRoot 'toolchains\llvm\prebuilt\windows-x86_64\bin\llvm-readelf.exe'
  $symbols=& $readelf --dyn-syms --wide $library
  if($LASTEXITCODE){throw 'Could not inspect Android exports.'}
  $required=@('nfa_core_open','nfa_core_close','nfa_core_step','nfa_core_pause','nfa_core_timing','nfa_core_pixels','nfa_core_state_size','nfa_core_load_state','nfa_core_save_state','nfa_core_read_audio','nfa_touch_clear','nfa_touch_set','nfa_touch_keys','nfa_core_battery_size','nfa_core_copy_battery','nfa_core_load_battery')
  if($Jni){
   foreach($method in @('openNative','closeNative','stepNative','pauseNative','timingNative','frameNative','audioNative','snapshotNative','restoreNative','captureSupportedNative','captureEnableNative','captureStatsNative','capturePacketNative','captureLayersNative','captureSceneNative')){
    $required+=('Java_org_codex_nfsugpreview_NativeCore_'+$method)
   }
  }
  $exports=$symbols -join [Environment]::NewLine
  foreach($symbol in $required){if($exports -notmatch ('\b'+$symbol+'\b')){throw "Missing Android export $symbol"}}
  $symbols|Set-Content -LiteralPath (Join-Path $OutputRoot ('exports-'+$abi+'.txt')) -Encoding UTF8
  $results+=@{abi=$abi;api=$Api;library=$library;bytes=$bytes.Length;machine=$machine;exports_checked=$required.Count;sha256=([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','')}
  Write-Output "Verified Android $abi ELF and $($required.Count) portable API exports."
 }
 $report=@{status='COMPILED_ANDROID_CORE_COMPONENT';ndk=$NdkRoot;ndk_properties=(Get-Content -LiteralPath (Join-Path $NdkRoot 'source.properties') -Raw);mgba_source=$MgbaSource;project_inputs=$inputs;targets=$results;jni_built=[bool]$Jni;apk_built=$false;android_runtime_verified=$false;native_renderer_integrated=$false;touch_overlay_ui_built=$false;scope='Core/input/audio/state API cross-compilation only; not an installable APK or verified Android gameplay.'}
 $report|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $OutputRoot 'android-build-report.json') -Encoding UTF8
}finally{$sha.Dispose()}
