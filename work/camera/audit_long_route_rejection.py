from pathlib import Path
import ctypes as C,json
p=Path('work/camera').resolve();d=C.CDLL(str(p/'visibility-probe-wide.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t);d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p];d.nf_live_visibility_enable.argtypes=[C.c_void_p,C.c_size_t,C.c_size_t]
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');received=0
@Sink
def sink(context,epoch,data,size):
 global received
 received+=1;return 1
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(p.parent/'driving.state').encode(),0)
try:
 assert d.nf_native_scene_sink(sink,None);b=rom.read_bytes();assert d.nf_live_visibility_enable(b,len(b),16*1024*1024);d.nf_live_surface_audit_enable(1)
 stats=(C.c_uint32*4)()
 for i in range(3583):
  d.nf_frame(1|(32 if 180<=i<500 else 16 if 500<=i<720 else 0));d.nf_native_scene_stats(stats)
  if stats[2]:
   detail=(C.c_uint32*9)();model=(C.c_uint32*8)();assembly=(C.c_uint32*3)();d.nf_native_scene_rejection_detail(detail);d.nf_native_model_rejection_detail(model);d.nf_live_native_model_assembly_stats(assembly)
   r=dict(result='REPRODUCED_FAILURE',input_refresh_index=i,original_refreshes=i+1,published=received,scene_stats=list(stats),scene_detail=list(detail),model_detail=list(model),native_model_assembly_stats=list(assembly),scope='First deterministic rejection from60sec route; diagnostic evidence, no completion claim')
   visits=(C.c_uint32*(1+16*7))();d.nf_native_scene_model_rejection_visits(visits);r['model_draw_visits']=[list(visits)[1+j*7:1+(j+1)*7] for j in range(min(visits[0],16))];r['model_draw_count']=visits[0]
   assert d.nf_state(str(p/'long-route-first-reject.state').encode(),1);(p/'long-route-rejection.json').write_text(json.dumps(r,indent=2));print(r);break
 else:raise AssertionError('Rejected scene not reproduced')
finally:d.nf_close()
