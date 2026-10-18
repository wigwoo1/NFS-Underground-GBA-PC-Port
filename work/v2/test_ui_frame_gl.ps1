param([string]$VsDevCmdPath='C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\Tools\VsDevCmd.bat')
$ErrorActionPreference='Stop'
if(!(Test-Path -LiteralPath $VsDevCmdPath)){throw "Visual Studio developer command file not found: $VsDevCmdPath"}
$tmp=Join-Path $env:TEMP 'nfsug-ui-gl-test'
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
$exe=Join-Path $tmp 'test_ui_frame_gl.exe'
$log=Join-Path $tmp 'build.log'
$cmd=Join-Path $tmp 'build.cmd'
$src=$PSScriptRoot
$body=@"
@echo off
call "$VsDevCmdPath" -arch=x64 -host_arch=x64
if errorlevel 1 exit /b 1
cl.exe /nologo /O2 /MD /W3 /std:c11 /D_CRT_SECURE_NO_WARNINGS /TC /I"$src" /Fe:"$exe" "$src\test_ui_frame_gl.c" "$src\ui_scale.c" "$src\texture_pack.c" "$src\ui_gl_texture.c" /link opengl32.lib gdi32.lib user32.lib > "$log" 2>&1
exit /b %errorlevel%
"@
[IO.File]::WriteAllText($cmd,$body,[Text.Encoding]::ASCII)
& cmd.exe /d /c $cmd
if($LASTEXITCODE){Get-Content -LiteralPath $log -Tail 80;throw 'OpenGL UI cache test build failed.'}
& $exe
if($LASTEXITCODE){throw 'OpenGL UI cache test failed.'}