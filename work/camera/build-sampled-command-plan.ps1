$ErrorActionPreference='Stop'
$nfCompiler='C:/NFSUG-Workspace/2026-09-13/make/work/toolchain/w64devkit/bin'
& "$nfCompiler/gcc.exe" "-B$nfCompiler/" -O2 -Wall -Wextra -Werror -shared -DNF_VISIBILITY_QUEUE_CAPACITY=32 work/camera/sampled_command_plan.c work/camera/ordered_dispatch.c -o work/camera/sampled-command-plan-test.dll
exit $LASTEXITCODE
