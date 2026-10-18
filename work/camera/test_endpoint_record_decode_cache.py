import runpy,time,json,threading
from pathlib import Path
import owned_motion_pairs as m
v=runpy.run_path('work/camera/test_external_fullscene_transition.py');frames=v['frames'];checks=0
for frame in frames:
 assert m.records(frame)==m._decode_records(frame)
 a=m.records(frame);a['records'][0]['blocks'].clear();a['records'].clear();assert m.records(frame)==m._decode_records(frame)
 mutable=bytearray(frame);assert m.records(mutable)==m._decode_records(mutable)
 errors=[]
 def other():
  try:assert not hasattr(m._record_cache,'entries');assert m.records(frame)==m._decode_records(frame)
  except BaseException as e:errors.append(repr(e))
 t=threading.Thread(target=other);t.start();t.join();assert not errors
 for _ in range(6):m.records(bytes(bytearray(frame)))
 assert len(m._record_cache.entries)<=4;checks+=1
samples=[]
for fn in (m._decode_records,m.records):
 start=time.perf_counter_ns()
 for i in range(400):fn(frames[i%2])
 samples.append((time.perf_counter_ns()-start)/1e6)
result=dict(exact_endpoint_decodes=checks,mutable_containers_isolated=True,thread_isolation=True,bound=4,uncached_ms=samples[0],cached_ms=samples[1],scope='endpoint decode component; live timing unverified')
Path('work/camera/prototype-runs/endpoint-record-decode-cache.json').write_text(json.dumps(result,indent=2));print(result)
