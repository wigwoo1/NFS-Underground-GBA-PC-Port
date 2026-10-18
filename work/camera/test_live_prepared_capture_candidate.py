import runpy,json,statistics,time
from pathlib import Path
import _owned_frame_capture_profile_candidate as original
import owned_prepared_frame_service_candidate as service_module
import _owned_frame_capture_prepared_profile_candidate as diagnostic
service_module.native=diagnostic
service=service_module.PreparedFrames()
saved_capture=original.capture;saved_profile=original.last_profile;rows=[]
def capture(*args):
 start=time.perf_counter_ns();packet=service.capture(*args);end=time.perf_counter_ns();s=diagnostic.stats()
 assert s[6]==len(packet) and 0<=s[4]<=s[3]
 if len(rows)<20:assert packet==saved_capture(*args)
 rows.append(dict(bytes=s[6],moved=bool(s[0]),resize_ms=s[1]*1000/s[2],resident_fraction=s[4]/s[3],read_ms=s[5]*1000/s[2],caller_ms=(end-start)/1e6))
 return packet
original.capture=capture
# This variant has a separate seven-field diagnostic, not the original fifteen-field profile.
original.last_profile=lambda:()
try:
 runpy.run_path('work/camera/run_native_async_private_capture_candidate.py',run_name='__main__')
 assert len(rows)>100
finally:
 shutdown=service.close();original.capture=saved_capture;original.last_profile=saved_profile
result=dict(result='PASS_LIVE_PREPARED_CAPTURE_PARITY_RESIDENCY',captures=len(rows),parity_frames=20,shutdown=shutdown,moved=sum(r['moved'] for r in rows),medians={k:statistics.median(r[k] for r in rows) for k in ('resize_ms','resident_fraction','read_ms','caller_ms')},rows=rows,scope='Actual game prepared capture; first20 match existing private capture. Diagnostic residency queries and duplicate parity captures perturb timing; no matched performance or60fps claim. Original15field profile intentionally absent.')
assert shutdown['joined'] and shutdown['pending']==0 and shutdown['peak']<=2
Path('work/camera/prototype-runs/live-prepared-residency-20261009.json').write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='rows'})
