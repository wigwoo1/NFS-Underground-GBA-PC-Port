"""Validate native QPC phase chronology on the complete long-interval ledger."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text())
ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals']
assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
rows=[]
for gap in ledger['records']:
 stages=[s for s in gap['consumer_stages'] if s['stage']=='ordered_sky_world_hud']
 assert len(stages)==1
 s=stages[0];t=s['native_tail_ticks']
 assert len(t)==7 and all(type(v) is int and v>0 for v in t)
 assert all(a<=b for a,b in zip(t[1:],t[2:]))
 native_ns=(t[6]-t[1])*1e9/t[0]
 assert native_ns<=s['elapsed_ns']+1000
 values={n:(t[b]-t[a])*1000/t[0] for n,a,b in [('sky_ms',1,2),('world_ms',3,4),('hud_ms',5,6),('sky_to_world_ms',2,3),('world_to_hud_ms',4,5)]}
 assert abs(sum(values.values())-native_ns/1e6)<1e-6
 rows.append(dict(display_index=gap['display_index'],interval_ms=gap['interval_ns']/1e6,outer_tail_ms=s['elapsed_ns']/1e6,native_tail_ms=native_ns/1e6,**values))
out=dict(result='PASS_COMPLETE_NATIVE_TAIL_PHASES',long_intervals=len(rows),rows=rows,scope='Complete retained >33.333ms API intervals; elapsed includes driver and scheduling, not exclusive GPU/CPU time, fidelity or visible60/scanout proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
