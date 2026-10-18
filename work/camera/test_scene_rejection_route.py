from pathlib import Path
import ctypes as C,json,hashlib
p=Path('work/camera').resolve();root=p.parent;rom=b'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba'
d=C.CDLL(str(p/'visibility-probe-wide.dll'));d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int]
Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t)
packets=[]
@Sink
def sink(user,epoch,ptr,size):packets.append(hashlib.sha256(C.string_at(ptr,size)).hexdigest());return 1
d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p];assert d.nf_init(rom,b'') and d.nf_state(str(root/'driving.state').encode(),0) and d.nf_native_scene_sink(sink,None)
rows=[];last=0
try:
 for i in range(1800):
  d.nf_frame(1|(32 if 180<=i<500 else 16 if 500<=i<720 else 0));stats=(C.c_uint32*4)();d.nf_native_scene_stats(stats)
  if stats[2]!=last:
   detail=(C.c_uint32*9)();d.nf_native_scene_rejection_detail(detail);model=(C.c_uint32*8)();d.nf_native_model_rejection_detail(model);rows.append(dict(refresh=i+1,serial=detail[0],begin=detail[1],end=detail[2],page=detail[3],failed=detail[4],surfaces=detail[5],commands=detail[6],model_present=detail[7],bounds=detail[8],model_capture=list(model)));last=stats[2]
 report=dict(scope='Deterministic original scene assembly rejection diagnosis,1800refresh accelerate/left/right route',stats=list(stats),rejections=rows,packet_count=len(packets))
 assert not rows and stats[0]==stats[1]==len(packets) and stats[3]==0,report
 Path(p/'scene-rejection-route-tests.json').write_text(json.dumps(report,indent=2));print(report)
finally:d.nf_close()
