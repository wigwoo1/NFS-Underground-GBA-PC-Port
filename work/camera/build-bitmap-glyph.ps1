$ErrorActionPreference='Stop'
$nfCompiler='C:/NFSUG-Workspace/2026-09-13/make/work/toolchain/w64devkit/bin'
& "$nfCompiler/gcc.exe" "-B$nfCompiler/" -O2 -Wall -Wextra -Werror -shared work/camera/bitmap_glyph.c -o work/camera/bitmap-glyph.dll
exit $LASTEXITCODE
