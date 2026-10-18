from pathlib import Path
import hashlib
from owned_sample_signature import signature
import owned_motion_visibility as visibility
import owned_sampled_world_frame as assembly
from owned_native_frame_join import join_frame as native_join
original_join=assembly.join_frame
setup=Path('work/camera/test_prepared_world_motion.py').read_text().split('try:\n for fa,fb')[0]
exec(compile(setup,'fullscene_fixture','exec'))
checks=[]
try:
 for fa,fb in zip(r['wall_diagnostic_frames'],r['wall_diagnostic_frames'][1:]):
  a=ClosedGraph.decode(Path(fa['graph']).read_bytes());b=ClosedGraph.decode(Path(fb['graph']).read_bytes());sa=ClosedSupplements.decode(Path(fa['supplements']).read_bytes(),a);sb=ClosedSupplements.decode(Path(fb['supplements']).read_bytes(),b)
  prepared=PreparedWorldMotion(Path(fa['regenerated']).read_bytes(),Path(fb['regenerated']).read_bytes(),MotionScene(a,sa),MotionScene(b,sb),history,old_roads,rom)
  try:
   for alpha in (.25,.5,.75):
    outputs=[]
    for cached in (False,True):
     assembly.join_frame=native_join if cached else original_join;prepared.pair.portal._samples.clear()
     sample=prepared.sample(alpha);frame,camera,models,bounds,_=sample
     assert d.nf_owned_gpu_draw_surface_clips(frame,len(frame),camera,models,bounds,len(records(frame)['records']))==0
     assert d.nf_owned_gpu_read(rgb,len(rgb))==0
     outputs.append((signature(sample),hashlib.sha256(rgb.raw).hexdigest()))
    assert outputs[0]==outputs[1]
    checks.append(dict(older=a.refresh,newer=b.refresh,alpha=alpha,all_buffers_exact=True,full_4k_rgb_exact=True))
  finally:prepared.close()
  old_roads,_=history.plan(b)
finally:
 assembly.join_frame=original_join;history.close();assert d.nf_owned_gpu_close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/queued-frame-join-parity-20261007');cp.mkdir(exist_ok=True);(cp/'fullscene-tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='45 intermediate complete sampled buffer/4K RGB parity against Python bytes join; native copy releases GIL; no live throughput claim; replay not live cadence or independent full fidelity'),indent=2));print('PASS',len(checks),'complete buffer and 4K comparisons')
