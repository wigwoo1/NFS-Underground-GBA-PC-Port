param(
 [string]$OutputRoot='C:\NFSUG-Workspace\NFSUG-android-local',
 [string]$CompilerBin='C:\msys64\mingw64\bin'
)
$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$false
$package=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\v2\package\NFSUG-Native-Renderer-source'))
$archive=Join-Path $package 'build\mgba-nfsug\libmgba.a'
$compiler=Join-Path $CompilerBin 'gcc.exe'
if(!(Test-Path -LiteralPath $archive) -or !(Test-Path -LiteralPath $compiler)){throw 'Missing existing Windows core archive or MinGW compiler.'}
[IO.Directory]::CreateDirectory($OutputRoot)|Out-Null
$env:PATH=$CompilerBin+';'+$env:PATH
$dll=Join-Path $OutputRoot 'nfsug_android_core_host.dll'
& $compiler -O2 -shared -DBUILD_STATIC -DM_CORE_GBA -DUSE_DEBUGGERS "-I$(Join-Path $package 'deps\mgba-0.10.5\include')" "-I$(Join-Path $package 'build\mgba-nfsug\include')" (Join-Path $PSScriptRoot 'nfsug_android_core.c') $archive -lws2_32 -lshlwapi -lole32 -luuid '-Wl,--gc-sections' -o $dll
if($LASTEXITCODE){throw 'Portable host component compilation failed.'}
Write-Output "Built Windows-only equivalence component: $dll"
