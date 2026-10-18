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
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());d=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_draw_surface_clips.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];rgb=C.create_string_buffer(3840*2160*3);checks=[];endpoint_count=0;interior_count=0;prepare_ns=[];sample_ns=[];completed_ns=[];draw_ns=[];finish_ns=[]
d.nf_owned_gpu_texture_stats.argtypes=[C.POINTER(C.c_uint64)];texture_samples=[]
def texture_stats():
 values=(C.c_uint64*6)();assert d.nf_owned_gpu_texture_stats(values)==0;return list(values)
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
    textures_before=texture_stats();draw_begin=time.perf_counter_ns();assert d.nf_owned_gpu_draw_surface_clips(frame,len(frame),camera,models,bounds,detail['geometry_records'])==0;draw_end=time.perf_counter_ns();assert d.nf_owned_gpu_finish()==0;finished=time.perf_counter_ns();completed_ns.append(finished-begin);draw_ns.append(draw_end-draw_begin);finish_ns.append(finished-draw_end);textures_after=texture_stats();texture_samples.append(dict(older=a.refresh,newer=b.refresh,alpha=alpha,counters=textures_after,delta=[y-x for x,y in zip(textures_before,textures_after)]))
    assert d.nf_owned_gpu_read(rgb,len(rgb))==0;interior_count+=1
    base,_,original_models=motion.sample(alpha);model_index=next(i for i,row in enumerate(records(base)['records']) if row['kind']==3);assembled_model_index=next(i for i,row in enumerate(records(frame)['records']) if row['kind']==3)
    assert list(models[assembled_model_index*12:assembled_model_index*12+12])==list(original_models[model_index*12:model_index*12+12])
   samples.append(dict(alpha=alpha,**detail))
  checks.append(dict(older=a.refresh,newer=b.refresh,samples=samples))
  old_roads,_=history.plan(b)
  prepared.close()
finally:history.close();assert d.nf_owned_gpu_close()
out=dict(texture_counter_names=['uploads','hits','evictions','uploaded_bytes','resident_bytes','ordinal_hint_hits'],texture_samples=texture_samples,result='MEASURE_COMPLETED_WORLD_FRAME',completed_ms=[x/1e6 for x in completed_ns],draw_cpu_ms=[x/1e6 for x in draw_ns],gpu_finish_wait_ms=[x/1e6 for x in finish_ns],completed_p95_ms=sorted(completed_ns)[int(.95*(len(completed_ns)-1))]/1e6,completed_max_ms=max(completed_ns)/1e6,frames_over_60hz_budget=sum(x>1e9/60 for x in completed_ns),prepare_ms=[x/1e6 for x in prepare_ns],sample_ms=[x/1e6 for x in sample_ns],sample_cpu_p95_ms=sorted(sample_ns)[int(.95*(len(sample_ns)-1))]/1e6,sample_cpu_max_ms=max(sample_ns)/1e6,endpoint_frames_pixel_exact=endpoint_count,intermediate_gpu_frames=interior_count,checks=checks,scope='Fullscene sampled main roads/walls and supplemental wall visibility, independent world surface order; retained car anchor/HUD. CPU sample+draw+glFinish completion timing excludes readback and present/scanout; fractional oracle/object placement/live cadence pending.')
Path('work/camera/completed-world-frame-timing.json').write_text(json.dumps(out,indent=2));print(out['result'],endpoint_count,interior_count,'completed p95 ms',out['completed_p95_ms'],'max',out['completed_max_ms'],'over budget',out['frames_over_60hz_budget'])

