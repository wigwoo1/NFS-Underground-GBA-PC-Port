from pathlib import Path
import runpy,ctypes as C,struct,json
p=Path('work/camera');ns=runpy.run_path(str(p/'test_road_texture_indices.py'));d=ns['d'];U=C.c_uint32;P=C.c_void_p
class Command(C.Structure):
 _fields_=[('head',U*13),('record',C.c_uint8*16),('state',C.c_uint8*256),('model',C.c_uint8*68),('billboard',U*18),('vertex_count',U),('edge',C.c_uint8*52),('vertices',C.c_int32*(128*6)),('bounds',C.c_uint16*4),('cell_end',U)]
fn=d.nf_scene_command_road_indices_owned;fn.argtypes=[P,ns['Read'],P,C.POINTER(P),C.POINTER(U),C.POINTER(U)]
state=ns['state'];struct.pack_into('<I',state,0,0x02004000);material=ns['material'];struct.pack_into('<H',material,26,3);struct.pack_into('<H',material,10,8)
packed=bytes([0,1,127,255]*16);ns['regions'][0x02004000]=packed
command=Command();command.head[0]=1;command.head[5]=0x02001000;C.memmove(command.state,bytes(state),256)
# Destroy external state: extraction must use the owned command state overlay.
state[:]=bytes(256);out=P();w=U();h=U();assert fn(C.byref(command),ns['read'],None,C.byref(out),C.byref(w),C.byref(h))
try:assert (w.value,h.value)==(8,4) and C.string_at(out,32)==b''.join(packed[y*16:y*16+8] for y in range(4))
finally:d.nf_surface_free(out)
guards=0
for kind,secondary,source in [(2,0,0x02001000),(1,1,0x02001000),(1,0,0x02009900)]:
 command.head[0]=kind;command.head[8]=secondary;command.head[5]=source;out=P(123);w=U(456);h=U(789)
 assert not fn(C.byref(command),ns['read'],None,C.byref(out),C.byref(w),C.byref(h));assert (out.value,w.value,h.value)==(123,456,789);guards+=1
report=dict(result='PASS',owned_command_state_used=True,original_index_bytes=32,atomic_rejections=guards,scope='Primary road command-owned state extraction; full scene producer/live routing pending.')
(p/'command-road-indices-tests.json').write_text(json.dumps(report,indent=2));print(report)
