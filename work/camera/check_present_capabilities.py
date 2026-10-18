"""Read actual current-context interop and compositor capabilities; no policy changes."""
import ctypes as C,json
from pathlib import Path
p=Path('work/camera').resolve();gpu=C.CDLL(str(p/'owned-sky-gpu.dll'));probe=C.CDLL(str(p/'owned-present-capabilities.dll'));probe.nf_present_capabilities.argtypes=[C.c_void_p]
try:
 assert gpu.nf_owned_gpu_window(0)==0
 values=(C.c_uint64*32)();assert probe.nf_present_capabilities(values)==0
 keys=['current_context','current_dc','window_owner_thread','dx_interop_extension','dx_interop2_extension','open_device','close_device','register_object','unregister_object','lock_objects','unlock_objects','share_handle','swap_interval_available','swap_interval_plus_one','composition_api','composition_hresult','composition_enabled','dwm_timing_api','dwm_timing_hresult','refresh_numerator','refresh_denominator','qpc_refresh_period','qpc_vblank','refresh_count','frame_count','frames_late','frames_outstanding']
 result=dict(zip(keys,values));assert result['current_context'] and result['current_dc'] and result['window_owner_thread']
finally:
 assert gpu.nf_owned_gpu_close() and gpu.nf_owned_gpu_active_contexts()==0 and gpu.nf_owned_gpu_query_pending()==0
result['cleanup_verified']=True;result['scope']='Actual hidden-window current GL context and Windows compositor capability snapshot; no shared resource, alternative backend or scanout verification.'
output=Path('work/camera/present-capabilities-20261007.json');output.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
