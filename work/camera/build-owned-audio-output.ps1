$ErrorActionPreference='Stop'
$nfCompiler='C:/NFSUG-Workspace/2026-09-13/make/work/toolchain/w64devkit/bin'
& "$nfCompiler/gcc.exe" "-B$nfCompiler/" -O2 -shared -D_WIN32_WINNT=0x0601 work/camera/owned_audio_output.c -lwinmm -o work/camera/owned-audio-output.dll
if($LASTEXITCODE){throw 'Owned audio output build failed'}
