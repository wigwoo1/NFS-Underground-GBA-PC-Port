"""Generate isolated borderless 3840x2160 source-context presentation."""
from pathlib import Path
p=Path('work/camera')
h=(p/'preview_resources.h').read_text()
a='DWORD style=preview_window_output?WS_OVERLAPPEDWINDOW:WS_OVERLAPPED;RECT bounds={0,0,preview_window_output?1280:16,preview_window_output?720:16};AdjustWindowRect(&bounds,style,FALSE);'
assert h.count(a)==1
h=h.replace(a,'DWORD style=preview_window_output?WS_POPUP:WS_OVERLAPPED;RECT bounds={0,0,preview_window_output?3840:16,preview_window_output?2160:16};AdjustWindowRect(&bounds,style,FALSE);')
a='preview_window=CreateWindowA('
assert h.count(a)==1
h=h.replace(a,'HANDLE(WINAPI*dpi_context)(HANDLE)=(void*)GetProcAddress(GetModuleHandleA("user32.dll"),"SetThreadDpiAwarenessContext");HANDLE previous_dpi=NULL;if(preview_window_output&&dpi_context)previous_dpi=dpi_context((HANDLE)(intptr_t)-4);\n '+a)
a='preview_dc=GetDC(preview_window);'
h=h.replace(a,'if(previous_dpi&&dpi_context)dpi_context(previous_dpi);'+a)
(p/'preview_resources_4k_candidate.h').write_text(h)
s=(p/'owned_gpu_source_context_candidate.c').read_text().replace('#include "preview_resources.h"','#include "preview_resources_4k_candidate.h"')
(p/'owned_gpu_source_context_4k_candidate.c').write_text(s)
