"""Raw-edge wall binding and sampled clip GPU component verification."""
from pathlib import Path
import ctypes as C,json,struct
from dataclasses import replace
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from sample_owned_motion import PreparedMotionPair
from owned_motion_visibility import PortalMotionPair
from owned_motion_wall_binding import bind_wall_records,sampled_bound_overrides
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);d=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_draw_wall_clips.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];rgb=C.create_string_buffer(3840*2160*3);checks=[]
try:
 for old,new in zip(r['wall_diagnostic_frames'],r['wall_diagnostic_frames'][1:]):
  a=ClosedGraph.decode(Path(old['graph']).read_bytes()).graph;b=ClosedGraph.decode(Path(new['graph']).read_bytes()).graph;frame=Path(old['regenerated']).read_bytes();motion=PreparedMotionPair(frame,Path(new['regenerated']).read_bytes());pair=PortalMotionPair(a,b,table,motion);closed=ClosedGraph.decode(Path(old['graph']).read_bytes());supplements=ClosedSupplements.decode(Path(old['supplements']).read_bytes(),closed);bindings=bind_wall_records(frame,pair,0,supplements);
  for field in ('epoch','refresh','source_refresh'):
   try:bind_wall_records(frame,pair,0,replace(supplements,**{field:getattr(supplements,field)+1}))
   except ValueError:pass
   else:raise AssertionError('Stale supplemental identity accepted')
  bounds,status=sampled_bound_overrides(frame,pair,bindings,0);array=(C.c_double*len(bounds))(*bounds)
  assert d.nf_owned_gpu_draw(frame,len(frame))==0;assert d.nf_owned_gpu_read(rgb,len(rgb))==0;expected=rgb.raw
  assert d.nf_owned_gpu_draw_wall_clips(frame,len(frame),None,None,array,len(bounds)//4)==0;assert d.nf_owned_gpu_read(rgb,len(rgb))==0;assert rgb.raw==expected
  intermediate=[]
  for alpha in (.25,.5,.75):
   bounds,status=sampled_bound_overrides(frame,pair,bindings,alpha);_,camera,models=motion.sample(alpha)
   if not status['disappeared_records']:
    array=(C.c_double*len(bounds))(*bounds);assert d.nf_owned_gpu_draw_wall_clips(frame,len(frame),camera,models,array,len(bounds)//4)==0
   intermediate.append(dict(alpha=alpha,**status))
  checks.append(dict(older=old['refresh'],newer=new['refresh'],graph_bound_records=sum(x['source'] is not None for x in bindings),unresolved_records=sum(x['status']=='unresolved_source_visit' for x in bindings),supplemental_bound_records=sum(x['status']=='owned_supplemental_edge' for x in bindings),endpoint_pixels_exact=8294400,intermediate=intermediate))
finally:assert d.nf_owned_gpu_close()
out=dict(result='PASS_RAW_WALL_BINDING_GPU_COMPONENT',checks=checks,scope='Existing-record clip override only. Unresolved supplemental visits and disappeared/new surfaces explicitly tracked; no complete scene visibility or live integration claim.')
Path('work/camera/sampled-wall-binding-gpu-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],len(checks),'unresolved',sum(x['unresolved_records'] for x in checks),'disappeared samples',sum(bool(s['disappeared_records']) for x in checks for s in x['intermediate']))
