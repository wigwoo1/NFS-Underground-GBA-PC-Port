"""Measure encoder-owned allocation on actual captured complete scenes."""
import json,time,tracemalloc,statistics,gc,hashlib
from pathlib import Path
from owned_process_preparation_service import encode_samples
setup=Path('work/camera/test_prepared_world_motion.py').read_text().split('try:\n for fa,fb')[0]
exec(compile(setup,'fixture','exec'))
checks=[]
try:
 for fa,fb in zip(r['wall_diagnostic_frames'],r['wall_diagnostic_frames'][1:]):
  a=ClosedGraph.decode(Path(fa['graph']).read_bytes());b=ClosedGraph.decode(Path(fb['graph']).read_bytes());sa=ClosedSupplements.decode(Path(fa['supplements']).read_bytes(),a);sb=ClosedSupplements.decode(Path(fb['supplements']).read_bytes(),b)
  prepared=PreparedWorldMotion(Path(fa['regenerated']).read_bytes(),Path(fb['regenerated']).read_bytes(),MotionScene(a,sa),MotionScene(b,sb),history,old_roads,rom)
  try:
   source={alpha:prepared.sample(alpha) for alpha in (.25,.5,.75)};measurements=[];reference=encode_samples(source)
   for mode in (False,True,True,False):
    gc.collect();tracemalloc.start();started=time.perf_counter_ns();encoded=encode_samples(source,borrow_tails=mode);elapsed=time.perf_counter_ns()-started;current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
    assert encoded==reference
    if mode:assert all(t.readonly and type(t.obj) is bytes for t in encoded['tails'])
    measurements.append(dict(borrowed=mode,current_bytes=current,peak_bytes=peak,encode_ms=elapsed/1e6,tail_bytes=sum(map(len,encoded['tails']))));del encoded
   baseline=statistics.median(x['peak_bytes'] for x in measurements if not x['borrowed']);candidate=statistics.median(x['peak_bytes'] for x in measurements if x['borrowed']);assert baseline>candidate
   checks.append(dict(source=[a.refresh,b.refresh],baseline_peak_bytes=baseline,candidate_peak_bytes=candidate,reduction_bytes=baseline-candidate,measurements=measurements))
  finally:prepared.close()
  old_roads,_=history.plan(b)
finally:
 if tracemalloc.is_tracing():tracemalloc.stop()
 history.close();assert d.nf_owned_gpu_close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/borrowed-tail-allocation-20261007');cp.mkdir(exist_ok=True)
result=dict(result='PASS',checks=checks,median_peak_reduction_bytes=statistics.median(x['reduction_bytes'] for x in checks),scope='Tracemalloc encoder-only Python allocations on preexisting captured complete samples, exact payload equality. Excludes source/native allocations and IPC/GPU/live pacing; timing instrumentation is intrusive.')
(cp/'allocation.json').write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='checks'})
