import json,struct,ctypes as C,time,statistics,cProfile,pstats,io
from owned_prepared_world_motion import PreparedWorldMotion
from owned_motion_scene import MotionScene
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
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());d=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_draw_surface_clips.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];rgb=C.create_string_buffer(3840*2160*3);checks=[];endpoint_count=0;interior_count=0;prepare_ns=[];sample_ns=[]
history=EndpointRoadPlanner(rom,table);old_roads,_=history.plan(ClosedGraph.decode(Path(r['wall_diagnostic_frames'][0]['graph']).read_bytes()))
try:
 for fa,fb in zip(r['wall_diagnostic_frames'],r['wall_diagnostic_frames'][1:]):
  a=ClosedGraph.decode(Path(fa['graph']).read_bytes());b=ClosedGraph.decode(Path(fb['graph']).read_bytes());sa=ClosedSupplements.decode(Path(fa['supplements']).read_bytes(),a);sb=ClosedSupplements.decode(Path(fb['supplements']).read_bytes(),b);old=Path(fa['regenerated']).read_bytes();new=Path(fb['regenerated']).read_bytes();motion=PreparedMotionPair(old,new);portal=PortalMotionPair(a.graph,b.graph,table,motion);pair=CompleteSupplementalCandidates(a,b,sa,sb,portal,rom);samples=[]
  begin=time.perf_counter_ns();prepared=PreparedWorldMotion(old,new,MotionScene(a,sa),MotionScene(b,sb),history,old_roads,rom);prepare_ns.append(time.perf_counter_ns()-begin)
  for alpha in (0,.25,.5,.75,1):
   begin=time.perf_counter_ns();frame,camera,models,bounds,detail=prepared.sample(alpha)
   if alpha not in (0,1):sample_ns.append(time.perf_counter_ns()-begin)
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
  if fb==r['wall_diagnostic_frames'][-1]:
   profile=cProfile.Profile();profile.enable();prepared.sample(.5);profile.disable();stream=io.StringIO();pstats.Stats(profile,stream=stream).sort_stats('cumulative').print_stats(14);Path('work/camera/prepared-world-sample-profile.txt').write_text(stream.getvalue());print(stream.getvalue())
  prepared.close()
finally:history.close();assert d.nf_owned_gpu_close()
out=dict(result='PASS_PREPARED_WORLD_MOTION',prepare_ms=[x/1e6 for x in prepare_ns],sample_ms=[x/1e6 for x in sample_ns],sample_cpu_p95_ms=sorted(sample_ns)[int(.95*(len(sample_ns)-1))]/1e6,sample_cpu_max_ms=max(sample_ns)/1e6,endpoint_frames_pixel_exact=endpoint_count,intermediate_gpu_frames=interior_count,checks=checks,scope='Fullscene sampled main roads/walls and supplemental wall visibility, independent world surface order; retained car anchor/HUD. Fractional visibility oracle, object placement, live cadence pending.')
Path('work/camera/prepared-world-motion-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],endpoint_count,interior_count,'sample p95 ms',out['sample_cpu_p95_ms'],'max',out['sample_cpu_max_ms'])
