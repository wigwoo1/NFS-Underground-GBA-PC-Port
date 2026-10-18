import json,sys
from pathlib import Path
from analyze_active_play_cadence import analyze
r=json.loads(Path(sys.argv[1]).read_text());rows=[x for x in r['presentation_samples'] if x.get('queued_wait_profile')];assert rows
for x in rows:
 p=x['queued_wait_profile'];w=x['native_wait_timing'];assert p[:3]==[w[0],w[2],w[1]] and p[7]==w[3] and p[5]<=p[6]
 assert p[1]>=p[0] and p[6]<=p[1]-p[0]
slow=sorted(rows,key=lambda x:x['queued_wait_profile'][1]-x['queued_wait_profile'][2],reverse=True)[:10]
out=dict(result='PASS',profiled_commits=len(rows),cadence=analyze(r),high_resolution_created=sum(x['queued_wait_profile'][8] for x in rows),fallback_created=sum(x['queued_wait_profile'][9] for x in rows),arm_failures=sum(x['queued_wait_profile'][10] for x in rows),wait_failures=sum(x['queued_wait_profile'][11] for x in rows),worst_waits=[dict(display_index=x['display_index'],profile=x['queued_wait_profile'],late_ms=(x['queued_wait_profile'][1]-x['queued_wait_profile'][2])/1e6,max_lock_ms=x['queued_wait_profile'][4]/1e6,max_wait_ms=x['queued_wait_profile'][5]/1e6) for x in slow],scope='Instrumented CPU deadline wait intervals include scheduling; no exclusive OS cause or scanout certification')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
