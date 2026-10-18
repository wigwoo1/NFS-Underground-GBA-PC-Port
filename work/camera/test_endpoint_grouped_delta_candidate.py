import sys,json,struct,threading
from pathlib import Path
sys.path.insert(0,str(Path('work/camera').resolve()))
from owned_portal_traversal import endpoint_delta as reference
import owned_endpoint_grouped_delta_candidate as candidate
setup=Path('work/camera/test_owned_portal_queue.py').read_text().split('checks=[]')[0];ns={};exec(compile(setup,'rawqueue','exec'),ns)
checks=0
for scene in ns['scenes'].values():
 raw=scene['matrix'];normal=tuple(v/16384 if i<9 else float(v) for i,v in enumerate(raw))
 for points,top,bottom in scene['graph'].values():
  for offset in range(0,len(points),68):
   x,z=struct.unpack_from('<2i',points,offset)
   for repeat in range(2):
    assert candidate.endpoint_delta(x,z,raw,normal)==reference(x,z,raw,normal);checks+=1
candidate.clear()
raw=next(iter(ns['scenes'].values()))['matrix'];normal=tuple(v/16384 if i<9 else float(v) for i,v in enumerate(raw))
for x in range(2050):assert candidate.endpoint_delta(x,0,raw,normal)==reference(x,0,raw,normal);checks+=1
assert candidate.stats()['point_entries']==2048 and candidate.stats()['bypassed']==2
before=candidate.stats();other=[]
def worker():
 other.append(candidate.stats());candidate.endpoint_delta(7,3,raw,normal)
t=threading.Thread(target=worker);t.start();t.join()
assert other[0]['point_entries']==0 and candidate.stats()==before
for offset in range(4):
 moved=raw[:-1]+(raw[-1]+offset,);norm=normal[:-1]+(normal[-1]+offset,)
 assert candidate.endpoint_delta(1,2,moved,norm)==reference(1,2,moved,norm)
 assert candidate.stats()['endpoint_owners']<=2 and candidate.stats()['point_entries']<=4096
out=dict(result='PASS_GROUPED_ENDPOINT_CORRECTION_EXACTNESS',checks=checks,bounded_overflow_exact=True,thread_isolation=True,stats=candidate.stats(),scope='Captured graph points plus overflow and endpoint-owner replacement; exact original correction tuple. No queue/full4K/spawn/live/GC gain proof.')
Path('work/camera/prototype-runs/endpoint-grouped-delta-20261009.json').write_text(json.dumps(out,indent=2));print(out)
