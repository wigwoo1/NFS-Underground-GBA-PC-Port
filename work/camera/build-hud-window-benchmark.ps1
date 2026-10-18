$ErrorActionPreference="Stop"
$nfCompiler="C:/NFSUG-Workspace/2026-09-13/make/work/toolchain/w64devkit/bin"
& "$nfCompiler/gcc.exe" "-B$nfCompiler/" -O2 -shared "-Wl,--export-all-symbols" work/camera/obj_tile.c work/camera/obj_scanline_benchmark.c -o work/camera/obj-tile-reference-benchmark.dll
if($LASTEXITCODE){throw "Reference component failed"}
& "$nfCompiler/gcc.exe" "-B$nfCompiler/" -O2 -shared "-Wl,--export-all-symbols" work/camera/obj_tile_window_candidate.c work/camera/obj_scanline_benchmark.c -o work/camera/obj-tile-window-benchmark.dll
if($LASTEXITCODE){throw "Candidate component failed"}

