import threading,json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import owned_road_planner_library_install_candidate
from owned_endpoint_road_planner import EndpointRoadPlanner
barrier=threading.Barrier(4)
def worker(index):
 a=EndpointRoadPlanner(b'',(0,)*32768);b=EndpointRoadPlanner(b'',(0,)*32768)
 assert a.d is b.d and a.ct is not b.ct
 a.scratch=a.d.nf_road_scratch_create();a.epoch=1;a.refresh=1
 assert a.scratch
 child=a.fork();assert child.d is a.d and child.scratch!=a.scratch
 pointer=a.scratch;child.close();assert a.scratch==pointer
 barrier.wait();result=(threading.get_ident(),id(a.d));a.close();b.close();assert a.scratch is None
 return result
with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(worker,range(4)))
assert len({x[1] for x in rows})==4
out=dict(result='PASS_THREAD_PRIVATE_WRAPPER_AND_SCRATCH',threads=rows,scope='Same-thread wrapper reuse, four simultaneous thread-private wrappers, real native scratch clone and independent destruction; captured full-scene/native4K tests separate.')
Path('work/camera/prototype-runs/road-planner-library-guards-20261009.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
