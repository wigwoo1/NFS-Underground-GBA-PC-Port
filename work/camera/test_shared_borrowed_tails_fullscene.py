from pathlib import Path
import hashlib,time,statistics,json
from multiprocessing.shared_memory import SharedMemory
import owned_shared_payload as transport
from owned_sample_signature import signature
from owned_process_preparation_service import encode_samples,ProcessSamples
setup=Path('work/camera/test_prepared_world_motion.py').read_text().split('try:\n for fa,fb')[0]
exec(compile(setup,'fixture','exec'))
checks=[];timings=[[],[]];sizes=[[],[]];memory=SharedMemory(create=True,size=64*1024*1024);serial=0
try:
 for fa,fb in zip(r['wall_diagnostic_frames'],r['wall_diagnostic_frames'][1:]):
  a=ClosedGraph.decode(Path(fa['graph']).read_bytes());b=ClosedGraph.decode(Path(fb['graph']).read_bytes());sa=ClosedSupplements.decode(Path(fa['supplements']).read_bytes(),a);sb=ClosedSupplements.decode(Path(fb['supplements']).read_bytes(),b)
  prepared=PreparedWorldMotion(Path(fa['regenerated']).read_bytes(),Path(fb['regenerated']).read_bytes(),MotionScene(a,sa),MotionScene(b,sb),history,old_roads,rom)
  try:
   source={alpha:prepared.sample(alpha) for alpha in (.25,.5,.75)};payload=encode_samples(source,borrow_tails=True);assert payload==encode_samples(source);assert all(isinstance(t,memoryview) and t.readonly and type(t.obj) is bytes for t in payload["tails"])
   for mode in (0,1,1,0,0,1,1,0):
    transport.DEDUPLICATE_BYTES=bool(mode);serial+=1;start=time.perf_counter_ns()
    descriptor=transport.write_payload(memory,payload,1,serial);restored=transport.read_payload(descriptor,1,memory)
    timings[mode].append((time.perf_counter_ns()-start)/1e6);sizes[mode].append(descriptor[3]);assert restored==payload
    decoded=ProcessSamples(restored)
    try:
     for alpha,value in source.items():
      assert signature(value)==signature(decoded.sample(alpha))
      checks.append(dict(older=a.refresh,newer=b.refresh,alpha=alpha,deduplication=bool(mode),full_buffers_exact=True))
    finally:decoded.close()
  finally:prepared.close()
  old_roads,_=history.plan(b)
finally:
 transport.DEDUPLICATE_BYTES=False;memory.close();memory.unlink();history.close();assert d.nf_owned_gpu_close()
out=dict(result='PASS',checks=checks,baseline_bytes=sum(sizes[0]),candidate_bytes=sum(sizes[1]),bytes_saved=sum(sizes[0])-sum(sizes[1]),baseline_median_transport_ms=statistics.median(timings[0]),candidate_median_transport_ms=statistics.median(timings[1]),scope='Borrowed immutable tail views through real captured changing fullscene payloads, actual shared mapping write/read, exact frame/camera/model/bounds/detail; alternating warm measurements exclude child IPC and live cadence')
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/shared-borrowed-tails-20261007');cp.mkdir(exist_ok=True);(cp/'tests.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='checks'})
