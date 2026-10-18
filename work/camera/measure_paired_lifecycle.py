"""Measured production paired native visibility assembly on menu/race checkpoints."""
import ctypes as C,json,struct,hashlib,os
from pathlib import Path
os.environ['NF_LIVE_ROAD_ATTRIBUTES']='1'
crt=C.CDLL('msvcrt');crt._putenv_s.argtypes=[C.c_char_p,C.c_char_p];assert crt._putenv_s(b'NF_LIVE_ROAD_ATTRIBUTES',b'1')==0
p=Path(__file__).resolve().parent;out=p/'prototype-runs/paired-lifecycle';out.mkdir(exist_ok=True);rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');raw=rom.read_bytes();P=C.c_void_p;Sink=C.CFUNCTYPE(C.c_int,P,C.c_uint64,P,C.c_size_t)
class Identity(C.Structure):_fields_=[('epoch',C.c_uint64),('serial',C.c_uint32),('begin',C.c_uint32),('end',C.c_uint32),('query',C.c_uint32),('builder',C.c_uint32)]
d=C.CDLL(str(p/'visibility-probe-wide.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_native_scene_sink.argtypes=[Sink,P];d.nf_live_visibility_enable.argtypes=[P,C.c_size_t,C.c_size_t];d.nf_scene_packet_free.argtypes=[P];d.nf_live_completed_native_multimodel_world_classified_pair_packet.argtypes=[P,P,C.c_double,P,P,P];reports=[]
paths=[p/'prototype-runs/menu-navigation/quick-1-release.state',p.parent/'fix-menu/stage-10.state',p/'prototype-runs/menu-navigation/quick-5-release.state']
for state in paths:
 before=hashlib.sha256(state.read_bytes()).hexdigest();ids=[];attempts=[];endpoint_checks=[]
 @Sink
 def sink(ctx,epoch,data,size):
  h=struct.unpack_from('<8I',C.string_at(data,32));ids.append(Identity(epoch,h[4],h[5],h[6],0,0));return 1
 assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0);assert d.nf_native_scene_sink(sink,None) and d.nf_native_scene_multimodel(1) and d.nf_live_visibility_enable(raw,len(raw),16*1024*1024);d.nf_live_surface_audit_enable(1);seen=0
 try:
  for frame in range(120):
   d.nf_frame(0)
   if len(ids)>seen and len(ids)>1:
    a,b=ids[-2:];packet=P();size=C.c_size_t();stage=C.c_uint();ok=d.nf_live_completed_native_multimodel_world_classified_pair_packet(C.byref(a),C.byref(b),0.5,C.byref(packet),C.byref(size),C.byref(stage));missing=(C.c_uint32*6)();reason=(C.c_uint32*4)();packet_detail=(C.c_uint32*6)();d.nf_live_command_palette_missing(missing);d.nf_scene_command_palette_detail(reason);d.nf_visibility_snapshot_packet_detail(packet_detail);model_missing=(C.c_uint32*6)();d.nf_live_paired_model_inputs_missing(model_missing);attempts.append(dict(frame=frame,serial=b.serial,ok=bool(ok),stage=stage.value,bytes=size.value,palette_missing=list(missing) if not ok else [],palette_reason=list(reason) if not ok else [],packet_detail=list(packet_detail),model_missing=list(model_missing) if not ok else []))
    if ok:
     data=C.string_at(packet,size.value);d.nf_scene_packet_free(packet)
     if sum(x['ok'] for x in attempts)==1:(out/(state.stem+'-paired-native.bin')).write_bytes(data)
   if len(ids)>seen and len(ids)>1:
    for fraction in [0.0,1.0]:
     endpoint=P();endpoint_size=C.c_size_t();endpoint_stage=C.c_uint();endpoint_ok=d.nf_live_completed_native_multimodel_world_classified_pair_packet(C.byref(ids[-2]),C.byref(ids[-1]),fraction,C.byref(endpoint),C.byref(endpoint_size),C.byref(endpoint_stage))
     endpoint_checks.append(dict(alpha=fraction,ok=bool(endpoint_ok),stage=endpoint_stage.value,bytes=endpoint_size.value))
     if endpoint_ok:d.nf_scene_packet_free(endpoint)
   seen=len(ids)
   hook=(C.c_uint32*12)();stats=(C.c_uint32*4)();deferred=(C.c_uint32*4)();d.nf_live_lifecycle_visibility_hooks(hook);d.nf_live_visibility_stats(stats);d.nf_live_deferred_surface_stats(deferred);ram=(C.c_uint8*0x48000)();registers=(C.c_uint32*16)();d.nf_live_lifecycle_builder_capture(ram,registers);(out/(state.stem+'-builder-source.bin')).write_bytes(bytes(ram));end_ram=(C.c_uint8*0x48000)();d.nf_live_lifecycle_builder_end_capture(end_ram);(out/(state.stem+'-builder-end-source.bin')).write_bytes(bytes(end_ram));diagnostics=dict(builder_registers=list(registers),hooks=list(hook),visibility=list(stats),deferred=list(deferred))
 finally:d.nf_close()
 assert hashlib.sha256(state.read_bytes()).hexdigest()==before;reports.append(dict(state=str(state),diagnostics=diagnostics,raw_packets=len(ids),paired_success=sum(x['ok'] for x in attempts),attempts=attempts,endpoint_checks=endpoint_checks));print(state.stem,len(ids),reports[-1]['paired_success'],sorted(set(x['stage'] for x in attempts)),flush=True)
(out/'report.json').write_text(json.dumps(dict(result='MEASURED',checks=reports,scope='Production alpha0.5 paired visibility assembly only, original neutral updates; no GPU/motion/timing claim.'),indent=2))
