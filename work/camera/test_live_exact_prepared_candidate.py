import runpy,json,time,statistics
from pathlib import Path
import _owned_frame_capture_profile_candidate as original
from owned_exact_prepared_service_candidate import ExactPreparedFrames
service=ExactPreparedFrames();saved_capture=original.capture;saved_profile=original.last_profile;rows=[]
def capture(*args):
 hits=service.hits;start=time.perf_counter_ns();packet=service.capture(*args);elapsed=(time.perf_counter_ns()-start)/1e6
 if len(rows)<20:assert packet==saved_capture(*args)
 rows.append(dict(bytes=len(packet),hit=service.hits>hits,caller_ms=elapsed));return packet
original.capture=capture;original.last_profile=lambda:()
try:
 runpy.run_path('work/camera/run_native_async_private_capture_candidate.py',run_name='__main__');assert len(rows)>100
finally:shutdown=service.close();original.capture=saved_capture;original.last_profile=saved_profile
assert shutdown['joined'] and shutdown['pending']==0 and shutdown['hits']+shutdown['misses']==len(rows)
result=dict(result='PASS_LIVE_EXACT_PREPARED_CAPTURE',captures=len(rows),parity_frames=20,shutdown=shutdown,hit_fraction=shutdown['hits']/len(rows),median_ms={kind:statistics.median(r['caller_ms'] for r in rows if r['hit']==flag) for kind,flag in [('hit',True),('miss',False)]},rows=rows,scope='Actual capture including size query and fallback. First20byteparity; capture15fieldprofile absent. Hit/miss subsets differ in source work, not causal timing comparison. Not fullscene60 proof.')
Path('work/camera/prototype-runs/live-exact-prepared-20261009.json').write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='rows'})
