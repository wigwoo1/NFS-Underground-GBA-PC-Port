"""Inspect actual loaded IWRAM material code without mutating ROM or save."""
from pathlib import Path
import sys,ctypes as C,json
setup=Path('work/camera/capture_motion_scanline_state.py').read_text().split('gpu=None;gpu_worker=None;gpu_checks=[]')[0]
exec(compile(setup,'capture_setup','exec'))
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0)
d.nf_capture_memory_read.argtypes=[C.c_uint,C.c_void_p,C.c_size_t];memory=C.create_string_buffer(0x8000)
assert d.nf_capture_memory_read(0x03000000,memory,len(memory))
folder=Path('work/camera/prototype-runs/runtime-material-code');folder.mkdir(exist_ok=True);(folder/'loaded-iwram.bin').write_bytes(memory.raw)
sys.path.insert(0,'work/tools')
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
out='\n'.join(f'{i.address:08x} {i.mnemonic} {i.op_str}' for i in Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(memory.raw[0x2368:0x2414],0x3002368))
(folder/'loaded-material.txt').write_text(out);print(out)
print('matches retained IWRAM:',memory.raw[0x2368:0x2414]==Path('work/camera/world-trace-0-iwram.bin').read_bytes()[0x2368:0x2414])
d.nf_scene_enable(1);d.nf_owned_slot_trace.argtypes=[C.c_char_p];assert d.nf_owned_slot_trace(str(folder/'slots.bin').encode())
for _ in range(120):d.nf_frame(1)
counts=(C.c_uint32*128)();d.nf_owned_material_hook_counts.argtypes=[C.c_void_p];d.nf_owned_material_hook_counts(counts)
seen={hex(0x03002300+i*4):n for i,n in enumerate(counts) if n};(folder/'hook-counts.json').write_text(json.dumps(seen,indent=2));print('material hook coverage',seen)
d.nf_owned_slot_trace(None);d.nf_close()
