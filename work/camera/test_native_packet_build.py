from pathlib import Path
import ctypes as C,json
class Section(C.Structure):_fields_=[('data',C.c_void_p),('size',C.c_size_t)]
class View(C.Structure):_fields_=[('serial',C.c_uint32),('begin',C.c_uint32),('end',C.c_uint32),('page',C.c_uint32),('sections',Section*5)]
root=Path('work/camera');d=C.CDLL(str((root/'scene_packet.dll').resolve()))
d.nf_scene_packet_view.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(View)]
d.nf_scene_packet_build.argtypes=[C.POINTER(View),C.POINTER(C.c_void_p),C.POINTER(C.c_size_t)]
d.nf_scene_packet_free.argtypes=[C.c_void_p]
checked=0;total=0
for path in sorted((root/'packet-sequence').glob('*.packet')):
 data=path.read_bytes();buffer=C.create_string_buffer(data);view=View();assert d.nf_scene_packet_view(buffer,len(data),C.byref(view))
 result=C.c_void_p();size=C.c_size_t();assert d.nf_scene_packet_build(C.byref(view),C.byref(result),C.byref(size))
 assert C.string_at(result,size.value)==data,path
 C.memset(buffer,0,len(data));assert C.string_at(result,size.value)==data,'Output aliases source'
 d.nf_scene_packet_free(result);checked+=1;total+=len(data)
assert checked==48
data=(root/'scene-packet.bin').read_bytes();buffer=C.create_string_buffer(data);valid=View();assert d.nf_scene_packet_view(buffer,len(data),C.byref(valid))
rejected=0
for mode in range(6):
 view=View.from_buffer_copy(bytes(valid))
 if mode==0:view.page=2
 elif mode==1:view.begin=view.end+1
 elif mode==2:view.sections[1].data=None
 elif mode==3:view.sections[2].size=0
 elif mode==4:view.sections[3].size=64*1024*1024
 else:view.sections[0].size-=1
 result=C.c_void_p(123);size=C.c_size_t(456)
 assert not d.nf_scene_packet_build(C.byref(view),C.byref(result),C.byref(size))
 assert result.value==123 and size.value==456;rejected+=1
report={'result':'PASS','packets_byte_identical_to_offline_export':checked,'total_bytes':total,'invalid_builds_rejected_without_output_changes':rejected,'scope':'Native assembly of already prepared sections; live geometry/material extraction remains unfinished.'}
(root/'native-packet-build-tests.json').write_text(json.dumps(report,indent=2));print(report)
