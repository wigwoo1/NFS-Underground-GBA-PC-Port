"""Verify captured original-cycle admission deadlines without treating late updates as smooth motion."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());samples=r['original_update_samples'];assert len(samples)==r['original_updates']
origins=set();late=[]
for i,s in enumerate(samples):
 expected=s['clock_origin']+((s['refresh']-s['clock_base']+1)*280896*1000000000+16777215)//16777216
 assert s['original_deadline_ns']==expected
 assert s['started_ns']>=expected,'Original game update admitted early'
 b=s['native_boundary'];assert s['started_ns']<=b[0]<=b[1]<=s['completed_ns'] and b[0]>=expected
 if i:assert s['refresh']==samples[i-1]['refresh']+1,'Original update skipped or repeated'
 origins.add(s['clock_origin']);late.append(s['started_ns']-expected)
out=dict(result='PASS_NO_EARLY_OR_SKIPPED_UPDATES',updates=len(samples),clock_origins=len(origins),pause_events=len(r['pause_events']),maximum_admission_lateness_ms=max(late)/1e6,scope='Captured original 16777216-Hz/280896-cycle deadline admission and sequential updates. Lateness remains and smooth60fps/scanout is not certified.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
