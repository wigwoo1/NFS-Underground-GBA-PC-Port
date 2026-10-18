import threading,struct,json
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
from owned_spatial_decode_cache_candidate import install,SpatialDescriptors,_local
install();barrier=threading.Barrier(4)
g=SimpleNamespace(geometry=struct.pack('<4I',7,1,0,0)+bytes(116),offsets=bytes(32))
def worker(i):
 a=SpatialDescriptors(g);barrier.wait();a.rows.clear()
 for j in range(100):
  b=SpatialDescriptors(g);assert 7 in b.rows
 return (threading.get_ident(),id(_local.entries),len(_local.entries))
with ThreadPoolExecutor(max_workers=4) as pool:rows=list(pool.map(worker,range(4)))
assert len({x[0] for x in rows})==4 and len({x[1] for x in rows})==4
print(json.dumps(dict(result='PASS_FOUR_THREAD_PRIVATE_CACHE',comparisons=400,threads=rows)))
