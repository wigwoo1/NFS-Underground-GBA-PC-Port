import runpy,json,threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import owned_visibility_buffers_candidate as candidate
import owned_wall_visibility_candidate as original
saved=[]
def checked(calls):
 a=candidate.reference(calls);b=candidate.batch(calls);assert a==b
 if len(saved)<10:saved.append(tuple(calls))
 return b
original.batch=checked
runpy.run_path('work/camera/test_combined_segmented_gpu.py',run_name='__main__')
assert len(saved)==10
for calls in saved:
 for subset in ((),calls[:1],calls[:3],calls,calls[:1]*4097):assert candidate.batch(subset)==candidate.reference(subset)
barrier=threading.Barrier(4)
def worker(i):
 expected=candidate.reference(saved[i]);first=candidate.batch(saved[i]);packed,out=candidate.buffers();identity=(threading.get_ident(),C.addressof(packed),C.addressof(out));barrier.wait()
 for j in range(30):assert candidate.batch(saved[(i+j)%len(saved)])==candidate.reference(saved[(i+j)%len(saved)])
 assert first==expected
 return identity
import ctypes as C
with ThreadPoolExecutor(max_workers=4) as pool:ids=list(pool.map(worker,range(4)))
assert len({x[1] for x in ids})==len({x[2] for x in ids})==4
Path('work/camera/visibility-buffer-boundaries.json').write_text(json.dumps(dict(result='PASS',captured_calls=len(saved),subset_and_fallback_cases=50,parallel_checks=120,private_threads=ids,scope='Captured calls and 4097-row fallback; immutable outputs retained across reuse and four private simultaneous buffers. Limited scenes, not physical timing.'),indent=2))
print('PASS captured boundaries, fallback and 4 private threads')
