"""Fresh-process captured preparation retained Python allocations, not RSS proof."""
import sys,json,tracemalloc,gc,time
from pathlib import Path
source=Path('work/camera/test_prepared_world_release_candidate.py').read_text().split('results=[]')[0]
exec(compile(source,'captured_setup','exec'))
from owned_precomputed_source_cached_library_candidate import source_library_owner,projection_table_owner
source_library_owner();projection_table_owner();gc.collect()
if sys.argv[1]=='decode':
 from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
cls=PreparedWorldMotion if sys.argv[1]=='baseline' else Candidate
history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh']
tracemalloc.start();start_current=tracemalloc.get_traced_memory()[0]
prepared=cls(*frames,*scenes,history,roads,rom)
constructed=tracemalloc.get_traced_memory()[0]
cached=PrecomputedSourceWorldSamples(prepared,alphas)
after_precompute=tracemalloc.get_traced_memory()[0]
cached.close();history.close();del cached,history
before_collect=tracemalloc.get_traced_memory()[0]
begin=time.perf_counter_ns();collected=gc.collect();elapsed=time.perf_counter_ns()-begin
after_collect,peak=tracemalloc.get_traced_memory()
assert prepared.history is None
out=dict(mode=sys.argv[1],constructed_bytes=constructed-start_current,closed_precomputed_bytes=after_precompute-start_current,retained_closed_prepared_bytes_before_collection=before_collect-start_current,retained_closed_prepared_bytes_after_collection=after_collect-start_current,peak_traced_bytes=peak,final_collection_objects=collected,final_collection_ns=elapsed,scope='Fresh process, one actual captured five-sample preparation; tracemalloc Python allocations excludes native GPU/driver/ROM preloaded allocations. No live memory bound or cadence proof.')
out['retained_allocation_sites']=[dict(site=str(row.traceback),bytes=row.size,count=row.count) for row in tracemalloc.take_snapshot().statistics('lineno')[:20]]
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out))
prepared.close()


