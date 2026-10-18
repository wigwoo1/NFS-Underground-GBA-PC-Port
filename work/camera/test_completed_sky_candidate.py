from pathlib import Path
from owned_sky_boundary import SkyBoundary,SceneSky
setup=Path('work/camera/capture_motion_scanline_state.py').read_text().split('gpu=None;gpu_worker=None;gpu_checks=[]')[0].replace("visibility-probe-wide.dll","sky-caller-probe.dll")
exec(compile(setup,'sky-candidate-setup','exec'))
os.environ['NF_CAPTURE_INDEXED_COPY']='1';assert crt._putenv(b'NF_CAPTURE_INDEXED_COPY=1')==0
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0);assert d.nf_native_scene_sink(text_scene_sink,None);raw=rom.read_bytes();assert d.nf_live_visibility_enable(raw,len(raw),16*1024*1024)
assert d.nf_world_trace(b'') and d.nf_layer_queue_enable(1) and d.nf_owned_graph_live_enable(1)
epoch=d.nf_native_scene_epoch();api=d.nf_live_completed_sky_read;api.argtypes=[C.c_uint64,C.c_uint,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)];found={};negative=0;associations=[]
publication_read=d.nf_live_completed_sky_publication_identity;publication_read.argtypes=[C.c_uint64,C.c_uint,C.c_void_p]
from owned_sky_capture import SkyCapture
asset_capture=SkyCapture(d,raw)
owned_assets=[]
identity_read=d.nf_live_completed_sky_identity;identity_read.argtypes=[C.c_uint64,C.c_uint,C.c_void_p]
try:
 for i in range(80):
  d.nf_frame(1)
  for serial in range(1,50):
   if serial in found:continue
   n=C.c_size_t()
   if not api(epoch,serial,0,None,0,C.byref(n)):continue
   assert n.value==15192
   buf=C.create_string_buffer(n.value);assert api(epoch,serial,0,buf,n.value,C.byref(n));b=SkyBoundary.decode(buf.raw)
   assert b.epoch==epoch and b.indices==raw[b.source-0x08000000:b.source-0x08000000+15136]
   # Rejected reads must leave caller-owned destination bytes unchanged.
   for ordinal,capacity in ((1,n.value),(0,n.value-1)):
    canary=C.create_string_buffer(b'\xa5'*n.value,n.value);before=canary.raw
    assert not api(epoch,serial,ordinal,canary,capacity,C.byref(n));assert canary.raw==before;negative+=1
   assert not api(epoch,serial,0,None,1,C.byref(n));negative+=1
   graph_read=d.nf_owned_graph_closed_read;graph_read.argtypes=[C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
   gn=C.c_size_t()
   graph_refresh=next((refresh for refresh in range(b.refresh,b.refresh+8) if graph_read(epoch,refresh,None,0,C.byref(gn))),None)
   if graph_refresh is not None:
    from owned_closed_graph import ClosedGraph
    gb=C.create_string_buffer(gn.value);assert graph_read(epoch,graph_refresh,gb,gn.value,C.byref(gn));g=ClosedGraph.decode(gb.raw)
    associations.append(dict(serial=serial,sky_refresh=b.refresh,publication_refresh=g.refresh,source_refresh=g.graph.refresh))
    assert g.epoch==b.epoch and g.graph.refresh<=b.refresh<=g.refresh
   identity=(C.c_uint32*3)();assert identity_read(epoch,serial,identity)
   assert identity[0]==serial and identity[1]<=b.refresh<=identity[2]
   exact=(C.c_uint32*3)();assert publication_read(epoch,g.refresh,exact);assert list(exact)==list(identity)
   canary=(C.c_uint32*3)(91,92,93);assert not publication_read(epoch+1,g.refresh,canary);assert list(canary)==[91,92,93];negative+=1
   sky_scene=SceneSky(b,*identity)
   assert sky_scene.match_graph(g) is sky_scene
   owned=asset_capture.read(g);assert owned.asset is not None;owned.asset.verify(b);owned_assets.append(owned)
   from dataclasses import replace
   try:sky_scene.match_graph(replace(g,refresh=g.refresh+1))
   except ValueError:negative+=1
   else:raise AssertionError('Wrong publication accepted')
   if associations and associations[-1]['serial']==serial:associations[-1]['native_identity']=list(identity)
   found[serial]=b
 assert found,'No completed sky captured'
 assert len(associations)==len(found),'Missing closed graph association'
 retained=next(iter(found.values())).encode()
 assert not api(epoch+1,next(iter(found)),0,None,0,C.byref(C.c_size_t()));negative+=1
 for i in range(80):d.nf_frame(1)
 assert not api(epoch,next(iter(found)),0,None,0,C.byref(C.c_size_t()));negative+=1
 assert d.nf_state(str(state).encode(),0)
 assert d.nf_native_scene_epoch()!=epoch
 assert not api(epoch,max(found),0,None,0,C.byref(C.c_size_t()));negative+=1
finally:d.nf_close()
assert SkyBoundary.decode(retained).encode()==retained
for owned in owned_assets:owned.asset.verify(owned.boundary)
import pickle
assert pickle.loads(pickle.dumps(owned_assets))==owned_assets
out=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-completed-sky-20261006');out.mkdir(parents=True,exist_ok=True)
(out/'tests.json').write_text(json.dumps(dict(result='PASS',records=len(found),epoch=epoch,negative_checks=negative,graph_associations=associations,scope='Actual completed native scene sky metadata/fullbytes copied to owned Python boundary, wrong epoch rejected, retainedbytes survive close; no renderer sky interpolation'),indent=2));print('PASS completed native sky',len(found),'negative',negative,'graph associations',len(associations))
