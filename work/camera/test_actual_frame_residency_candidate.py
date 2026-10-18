import runpy,json,statistics
from pathlib import Path
import _owned_frame_capture_profile_candidate as original
import _owned_frame_capture_residency_candidate as diagnostic
saved_capture=original.capture;saved_profile=original.last_profile;rows=[]
def capture(*args):
 packet=diagnostic.capture(*args);r=diagnostic.last_residency();p=diagnostic.last_profile()
 assert r[0]==len(packet) and r[1]==r[3] and 0<=r[2]<=r[1] and r[4]==r[3]
 rows.append(dict(bytes=r[0],pages=r[1],before=r[2],after=r[4],read_ms=(p[7]-p[6])*1000/p[12]))
 return packet
original.capture=capture;original.last_profile=diagnostic.last_profile
try:
 runpy.run_path('work/camera/run_native_async_private_capture_candidate.py',run_name='__main__')
 assert len(rows)>100
 result=dict(result='PASS_ACTUAL_PRIVATE_FRAME_PAGE_RESIDENCY',captures=len(rows),median_before_fraction=statistics.median(r['before']/r['pages'] for r in rows),median_read_ms=statistics.median(r['read_ms'] for r in rows),rows=rows,scope='QueryWorkingSetEx before/after actual sole-owned unpublished PyBytes capture. Diagnostic queries perturb scheduling; residency does not directly measure page-fault CPU cost or prove60fps.')
 Path('work/camera/prototype-runs/frame-residency-20261009.json').write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='rows'})
finally:original.capture=saved_capture;original.last_profile=saved_profile
