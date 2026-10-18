param([string]$CompilerBin='', [string]$CmakeExe='')
$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
if(!$CompilerBin){$cmd=Get-Command gcc -ErrorAction SilentlyContinue;if($cmd){$CompilerBin=Split-Path $cmd.Source}else{$CompilerBin='C:/msys64/mingw64/bin'}}
if(!$CmakeExe){$cmd=Get-Command cmake -ErrorAction SilentlyContinue;if($cmd){$CmakeExe=$cmd.Source}else{$CmakeExe='C:/Program Files/CMake/bin/cmake.exe'}}
if(!(Test-Path "$CompilerBin/gcc.exe") -or !(Test-Path $CmakeExe)){throw 'Supply -CompilerBin and -CmakeExe. See BUILDING.md.'}
$CompilerBin=[IO.Path]::GetFullPath($CompilerBin).Replace('\','/')
$env:PATH=$CompilerBin.Replace('/','\')+';'+$env:PATH
$makeProgram=Join-Path $CompilerBin 'mingw32-make.exe'
$generator='MinGW Makefiles'
if(!(Test-Path $makeProgram)){$makeProgram=Join-Path $CompilerBin 'make.exe'}
if(!(Test-Path $makeProgram)){$makeProgram=Join-Path $CompilerBin 'ninja.exe';$generator='Ninja'}
if(!(Test-Path $makeProgram)){throw 'No MinGW make or Ninja found beside GCC. Supply a complete compiler toolchain.'}
New-Item -ItemType Directory -Force build,deps | Out-Null
$mgbaBuild='build/mgba-nfsug'
if(!(Test-Path deps/mgba-0.10.5/CMakeLists.txt)){Expand-Archive -LiteralPath vendor/mgba-0.10.5.zip -DestinationPath deps}
$armPath=Join-Path $PSScriptRoot 'deps/mgba-0.10.5/src/arm/arm.c'
$armSource=[IO.File]::ReadAllText($armPath)
if(!$armSource.Contains('nfsArmHook')){
 $needle='static inline void ARMStep(struct ARMCore* cpu) {'
 if(!$armSource.Contains($needle)){throw 'Unexpected mGBA source; cannot apply instruction hook.'}
 $replacement="bool (*nfsArmHook)(struct ARMCore*) = NULL;`n$needle`n`tif (nfsArmHook && nfsArmHook(cpu)) return;"
 [IO.File]::WriteAllText($armPath,$armSource.Replace($needle,$replacement))
}
$argsConfigure=@('-S','deps/mgba-0.10.5','-B',$mgbaBuild,'-G',$generator,'-DCMAKE_POLICY_VERSION_MINIMUM=3.5',"-DCMAKE_C_COMPILER=$CompilerBin/gcc.exe","-DCMAKE_CXX_COMPILER=$CompilerBin/g++.exe","-DCMAKE_MAKE_PROGRAM=$makeProgram","-DCMAKE_C_FLAGS=-B$CompilerBin/","-DCMAKE_CXX_FLAGS=-B$CompilerBin/",'-DLIBMGBA_ONLY=ON','-DM_CORE_GB=OFF','-DUSE_DEBUGGERS=ON','-DUSE_GDB_STUB=OFF','-DBUILD_LTO=OFF','-DCMAKE_BUILD_TYPE=Release')
& $CmakeExe @argsConfigure
if($LASTEXITCODE){throw 'mGBA configure failed.'}
& $CmakeExe --build $mgbaBuild --target mgba -j 8
if($LASTEXITCODE){throw 'mGBA build failed.'}
$baseArgs=@("-B$CompilerBin/",'-O2','-ffunction-sections','-fdata-sections','-DBUILD_STATIC','-DM_CORE_GBA','-DUSE_DEBUGGERS','-DNF_VISIBILITY_CAPTURE','-DNF_ROAD_ATTRIBUTE_CORRECTION','-DNF_PACKET_NO_MAIN','-DNF_PACKET_NO_FILES','-D_GNU_SOURCE','-D_WIN32_WINNT=0x0600','-Ideps/mgba-0.10.5/include',"-I$mgbaBuild/include",'-Icamera','-Iv2')
$cameraSources=@(Get-Content 'camera/native-renderer-sources.txt' | Where-Object { $_ -and -not $_.StartsWith('#') } | ForEach-Object { $path=Join-Path 'camera' $_; if(!(Test-Path $path)){throw "Missing native renderer source: $path"};$path })
$links=@("$mgbaBuild/libmgba.a",'-lws2_32','-lshlwapi','-lole32','-luuid')
$hostArgs=$baseArgs+@('-mwindows','main.c','bridge.c','v2/gpu.c','v2/texture_pack.c','v2/ui_scale.c','native_span.c')+$cameraSources+$links+@('-Wl,--gc-sections','-lopengl32','-lgdi32','-lcomdlg32','-lwinmm','-o','build/NFSUG-Native-Renderer.exe')
& "$CompilerBin/gcc.exe" @hostArgs
if($LASTEXITCODE){throw 'Host build failed.'}
$bridgeArgs=$baseArgs+@('-DNF_PROBE_EXPORTS','-shared','bridge.c','native_span.c')+$cameraSources+$links+@('-Wl,--gc-sections','-lopengl32','-lgdi32','-lcomdlg32','-lwinmm','-o','build/nfsprobe.dll')
& "$CompilerBin/gcc.exe" @bridgeArgs
if($LASTEXITCODE){throw 'Bridge build failed.'}
& "$CompilerBin/gcc.exe" "-B$CompilerBin/" -O2 -shared native_span.c -o build/native_span.dll
if($LASTEXITCODE){throw 'Native routine build failed.'}
& "$CompilerBin/gcc.exe" "-B$CompilerBin/" -O2 tests/test_controller.c -o build/test_controller.exe
if($LASTEXITCODE){throw 'Controller test build failed.'}
& ./build/test_controller.exe
if($LASTEXITCODE){throw 'Controller mapping tests failed.'}
& "$CompilerBin/gcc.exe" "-B$CompilerBin/" -O2 -Iv2 tests/test_ui_scale.c v2/ui_scale.c -o build/test_ui_scale.exe
if($LASTEXITCODE){throw 'UI edge-aware upscaler tests failed.'}
& ./build/test_ui_scale.exe
if($LASTEXITCODE){throw 'UI edge-aware upscaler tests failed.'}
Write-Host 'Built build/NFSUG-Port-Lab.exe. See BUILDING.md for ROM and test commands.'
