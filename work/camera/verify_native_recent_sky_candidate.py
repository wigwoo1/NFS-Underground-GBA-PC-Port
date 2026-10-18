"""Recent captured sky phase fidelity only; never whole-run scanout evidence."""
import json,math,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());s=r['sky_capture_retention'];sources=r['sky_capture_records'];assert s['total_records']>240 and s['retained_records']==len(sources)==240 and s['dropped_records']==s['total_records']-240
by_identity={(x['epoch'],x['publication']):x for x in sources};assert len(by_identity)==len(sources)
checks=0
for row in r['presentation_samples']:
 if row['native_result']!=1:continue
 old=by_identity[row['epoch'],row['source_older']];new=by_identity[row['epoch'],row['refresh']]
 assert old['asset_origin']==new['asset_origin']
 delta=((new['angle']-old['angle']+8192)&16383)-8192
 phase=(((old['angle']&16383)+delta*row['alpha'])*240/4096)%240
 assert row['sky_phase_mode']=='continuous_angle' and math.isclose(row['sky_fraction'],phase-math.floor(phase),abs_tol=1e-10)
 checks+=1
assert checks>0
out=dict(result='PASS_RECENT_SKY_PHASE_RETENTION',retention=s,successful_recent_phase_checks=checks,scope='Only retained recent source/sample telemetry; whole-run source records truncated. No complete-run sky motion or independent pixel/scanout proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out))
