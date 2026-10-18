import json,struct,ctypes as C
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from owned_complete_supplemental_candidates import CompleteSupplementalCandidates
from owned_sampled_world_frame import assemble_world
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_sampled_road_sequence import SampledRoadSequence
from owned_motion_pairs import records
from sample_owned_motion import PreparedMotionPair
from owned_motion_visibility import PortalMotionPair
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());d=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_draw_surface_clips.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];rgb=C.create_string_buffer(3840*2160*3);checks=[];endpoint_count=0;interior_count=0
history=EndpointRoadPlanner(rom,table);old_roads,_=history.plan(ClosedGraph.decode(Path(r['wall_diagnostic_frames'][0]['graph']).read_bytes()))
try:
 for fa,fb in zip(r['wall_diagnostic_frames'],r['wall_diagnostic_frames'][1:]):
  a=ClosedGraph.decode(Path(fa['graph']).read_bytes());b=ClosedGraph.decode(Path(fb['graph']).read_bytes());sa=ClosedSupplements.decode(Path(fa['supplements']).read_bytes(),a);sb=ClosedSupplements.decode(Path(fb['supplements']).read_bytes(),b);old=Path(fa['regenerated']).read_bytes();new=Path(fb['regenerated']).read_bytes();motion=PreparedMotionPair(old,new);portal=PortalMotionPair(a.graph,b.graph,table,motion);pair=CompleteSupplementalCandidates(a,b,sa,sb,portal,rom);samples=[]
  fork=history.fork()
  try:new_roads,_=fork.plan(b)
  finally:fork.close()
  roads=SampledRoadSequence(a,b,portal,history)
  for alpha in (0,.25,.5,.75,1):
   frame,camera,models,bounds,detail=assemble_world(pair,roads,(old_roads,new_roads),alpha,rom)
   if alpha in (0,1):
    reference=new if alpha==1 else old
    assert d.nf_owned_gpu_draw(reference,len(reference))==0 and d.nf_owned_gpu_read(rgb,len(rgb))==0;expected=rgb.raw
    assert d.nf_owned_gpu_draw(frame,len(frame))==0 and d.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==expected;endpoint_count+=1
   else:
    assert d.nf_owned_gpu_draw_surface_clips(frame,len(frame),camera,models,bounds,len(records(frame)['records']))==0 and d.nf_owned_gpu_read(rgb,len(rgb))==0;interior_count+=1
    base,_,original_models=motion.sample(alpha);model_index=next(i for i,row in enumerate(records(base)['records']) if row['kind']==3);assembled_model_index=next(i for i,row in enumerate(records(frame)['records']) if row['kind']==3)
    assert list(models[assembled_model_index*12:assembled_model_index*12+12])==list(original_models[model_index*12:model_index*12+12])
   samples.append(dict(alpha=alpha,**detail))
  checks.append(dict(older=a.refresh,newer=b.refresh,samples=samples))
  old_roads,_=history.plan(b)
finally:history.close();assert d.nf_owned_gpu_close()
out=dict(result='PASS_SAMPLED_FULL_WORLD_DIAGNOSTIC',endpoint_frames_pixel_exact=endpoint_count,intermediate_gpu_frames=interior_count,checks=checks,scope='Fullscene sampled main roads/walls and supplemental wall visibility, independent world surface order; retained car anchor/HUD. Fractional visibility oracle, object placement, live cadence pending.')
Path('work/camera/sampled-full-world-diagnostic-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],endpoint_count,interior_count)
