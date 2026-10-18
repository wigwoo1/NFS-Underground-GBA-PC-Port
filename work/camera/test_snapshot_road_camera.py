"""Owned snapshot asset-provider path versus the previous classified packet."""
from pathlib import Path
import ctypes as C,struct,json,runpy,sys
p=Path('work/camera');sys.path.insert(0,str(p.resolve()));sys.argv=['oracle','0.5']
f=runpy.run_path(str(p/'test_classified_command_scene.py'));ns=f['ns'];d=ns['d'];P=C.c_void_p;Z=C.c_size_t;U=C.c_uint;Read=ns['Read'];Inputs=f['Inputs'];Palette=f['Palette']
Assets=C.CFUNCTYPE(C.c_int,P,U,P,Read,P,P,P,C.POINTER(P),C.POINTER(Z),C.POINTER(P),C.POINTER(Z))
extract=d.nf_extract_scene_command_full;extract.argtypes=[P,Read,P,P,P,C.POINTER(P),C.POINTER(Z),C.POINTER(P),C.POINTER(Z),P]
@Assets
def provider(ctx,i,c,read,user,rotation,out,a,az,l,lz):
 colors=ns['model_inputs'][48:]
 ok=extract(c,read,user,colors,rotation,a,az,l,lz,None)
 if ok:C.memmove(out,colors,512)
 return ok
assets=d.nf_visibility_assets_create(ns['rom'],len(ns['rom']));assert assets
selected=struct.unpack_from('<H',ns['iw'],0x5d44)[0]
snapshot=d.nf_visibility_snapshot_create(assets,ns['ew']+ns['iw'][:0x8000],0x48000,ns['address'],selected,selected,ns['pose'][:8],ns['pose'][8:56],ns['pose'][56:104]);assert snapshot
d.nf_visibility_assets_release(assets)
assert d.nf_visibility_snapshot_set_palette(snapshot,ns['model_inputs'][48:],512) and d.nf_visibility_snapshot_bind(snapshot,ns['identity'])
def build(name,callback,ctype,epoch):
 fn=getattr(d,name);fn.argtypes=[P,C.c_uint64,U,U,U,P,C.c_double,U,P,U,P,ctype,P,Inputs,P,C.POINTER(P),C.POINTER(Z)]
 out=P(123);size=Z(456)
 ok=fn(snapshot,epoch,ns['serial'],ns['begin_refresh'],ns['end_refresh'],ns['pose'],.5,ns['packet_header'][7],ns['initial_pool'],256,ns['model_inputs'][:48],callback,None,f['inputs'],None,C.byref(out),C.byref(size))
 if not ok:assert (out.value,size.value)==(123,456);return None
 try:return C.string_at(out,size.value)
 finally:d.nf_scene_packet_free(out)
try:
 old=build('nf_visibility_snapshot_packet_native_road_camera_model_inputs_at',f['palette'],Palette,ns['epoch'])
 new=build('nf_visibility_snapshot_packet_native_road_camera_model_inputs_at',f['palette'],Palette,ns['epoch'])
 assert old==new and len(new)>len((p/'road-attribute-produced.packet').read_bytes())
 assert build('nf_visibility_snapshot_packet_native_road_camera_model_inputs_at',f['palette'],Palette,ns['epoch']+1) is None
 @Assets
 def missing(*args):return 0
 assert build('nf_visibility_snapshot_packet_native_road_attributes_assets_model_inputs_at',missing,Assets,ns['epoch']) is None
 assert build('nf_visibility_snapshot_packet_native_road_camera_model_inputs_at',f['palette'],Palette,ns['epoch'])==new
finally:d.nf_visibility_snapshot_destroy(snapshot)
report=dict(result='PASS',exact_complete_snapshot_packet_bytes=len(new),atomic_epoch_and_resolver_rejections=2,repeat_after_failure_exact=True,scope='Identity-bound camera-aware snapshot producer repeatable; stale epoch rejected atomically. Legacy asset provider rejection also checked. Preview/live renderer/timing pending.')
(p/'snapshot-road-camera-tests.json').write_text(json.dumps(report,indent=2));print(report)
