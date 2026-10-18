#include "owned_gpu_input_probe.c"
__declspec(dllexport) int nf_owned_gpu_visibility(unsigned visible){if(visible>1||!preview_window||gpu_owner!=GetCurrentThreadId())return 31;ShowWindow(preview_window,visible?SW_SHOWNOACTIVATE:SW_HIDE);return IsWindowVisible(preview_window)==(BOOL)visible?0:39;}
