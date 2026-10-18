from pathlib import Path
import hashlib,time,statistics
from owned_sample_signature import signature
from owned_process_preparation_service import encode_samples,ProcessSamples
setup=Path('work/camera/test_prepared_world_motion.py').read_text().split('try:\n for fa,fb')[0]
exec(compile(setup,'fixture','exec'))
checks=[];timings=[[],[]];reuse=0
try:
 for fa,fb in zip(r['wall_diagnostic_frames'],r['wall_diagnostic_frames'][1:]):
  a=ClosedGraph.decode(Path(fa['graph']).read_bytes());b=ClosedGraph.decode(Path(fb['graph']).read_bytes());sa=ClosedSupplements.decode(Path(fa['supplements']).read_bytes(),a);sb=ClosedSupplements.decode(Path(fb['supplements']).read_bytes(),b)
  prepared=PreparedWorldMotion(Path(fa['regenerated']).read_bytes(),Path(fb['regenerated']).read_bytes(),MotionScene(a,sa),MotionScene(b,sb),history,old_roads,rom)
  try:
   source={alpha:prepared.sample(alpha) for alpha in (.25,.5,.75)};payload=encode_samples(source)
   for repeat in range(4):
    for mode in (repeat%2,1-repeat%2):
     ProcessSamples.reuse_immutable_frames=bool(mode);start=time.perf_counter_ns();decoded=ProcessSamples(payload);timings[mode].append((time.perf_counter_ns()-start)/1e6)
     try:
      for alpha,sample in source.items():assert signature(decoded.sample(alpha))==signature(sample)
      if repeat==0:
       if mode:reuse+=sum(x.get('immutable_frame_reused',False) for x in decoded.decode_stages)
       for alpha,sample in source.items():
        candidate=decoded.sample(alpha)
        images=[]
        for value in (sample,candidate):
         frame,camera,models,bounds,detail=value;assert d.nf_owned_gpu_draw_surface_clips(frame,len(frame),camera,models,bounds,detail['geometry_records'])==0 and d.nf_owned_gpu_read(rgb,len(rgb))==0;images.append(hashlib.sha256(rgb.raw).hexdigest())
        assert images[0]==images[1]
        checks.append(dict(older=a.refresh,newer=b.refresh,alpha=alpha,reuse_enabled=bool(mode),full_buffers_exact=True,full_4k_rgb_exact=True))
     finally:decoded.close()
  finally:prepared.close()
  old_roads,_=history.plan(b)
finally:ProcessSamples.reuse_immutable_frames=False;history.close();assert d.nf_owned_gpu_close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/process-reuse-fullscene-20261007');cp.mkdir(exist_ok=True)
out=dict(result='PASS',checks=checks,reused_frames=reuse,baseline_median_decode_ms=statistics.median(timings[0]),candidate_median_decode_ms=statistics.median(timings[1]),scope='15 changing captured intervals/45source samples, baseline and reuse decoded buffers+4Kimages exact; alternate warm decode benchmark excludes IPC/live scheduling')
(cp/'tests.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='checks'})
