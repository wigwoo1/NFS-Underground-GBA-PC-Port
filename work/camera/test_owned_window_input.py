from pathlib import Path
import ctypes as C,json
p=Path('work/camera');d=C.CDLL(str((p/'owned-world-gpu.dll').resolve()));f=d.nf_owned_pad_keys;f.argtypes=[C.c_uint,C.c_uint,C.c_uint,C.c_int,C.c_int];f.restype=C.c_uint
cases=[(0,0,0,0,0,0),(0x1000,0,0,0,0,1),(0x2000,0,0,0,0,2),(0,0,41,0,0,1),(0,41,0,0,0,2),(0,40,40,9000,-9000,0),(0,0,0,9001,0,16),(0,0,0,-9001,0,32),(0,0,0,0,9001,64),(0,0,0,0,-9001,128),(0x10|0x20|0x100|0x200,0,0,0,0,4|8|256|512),(0xf,0,0,0,0,16|32|64|128),(0x4000,0,0,0,0,512),(0x8000,0,0,0,0,256),(0,0,0,-32768,32767,32|64)]
for *args,expected in cases:assert f(*args)==expected,(args,expected,f(*args))
d.nf_owned_input_snapshot.argtypes=[C.c_void_p];state=(C.c_uint*4)();assert d.nf_owned_gpu_window(0)==0;assert d.nf_owned_input_poll();assert d.nf_owned_input_snapshot(state);assert state[0]==0 and state[1]==1 and state[2]==0;assert d.nf_owned_gpu_close()
r=dict(result='PASS_OWNED_WINDOW_INPUT_COMPONENT',synthetic_pad_cases=len(cases),hidden_unfocused_keys_cleared=True,hidden_focus_pause=True,physical_controller_connected=bool(state[3]),scope='Mapping thresholds/focus state component only. Live game input/pause clock integration andphysicalXboxdriving unverified.')
(p/'owned-window-input-tests.json').write_text(json.dumps(r,indent=2));print(r)
