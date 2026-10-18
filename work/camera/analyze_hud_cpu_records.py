"""Separate HUD wall durations/cycles; never assume a CPU clock frequency."""
import json,statistics,sys
from pathlib import Path
pool=json.loads(Path(sys.argv[1]).read_text());p=pool['hud_cpu_profile'];rows=[dict(zip(p['columns'],r)) for r in p['records']]
assert rows and p['dropped']==0 and all(r['ok'] and r['candidate_builds']==(0 if r['reuse'] else 160) for r in rows)
assert all(r[k]!=(2**64-1) for r in rows for k in ('lookup_wall_ns','lookup_cycles','prepare_wall_ns','prepare_cycles','prepare_thread_100ns'))
groups=[]
for reuse in (0,1):
 a=[r for r in rows if r['reuse']==reuse];assert a
 summary=dict(reuse=reuse,count=len(a),has_text=sum(r['has_text'] for r in a))
 for k in ('lookup_wall_ns','lookup_cycles','prepare_wall_ns','prepare_cycles','prepare_thread_100ns'):
  summary[k]=dict(median=statistics.median(r[k] for r in a),sum=sum(r[k] for r in a),maximum=max(r[k] for r in a))
 summary['largest_preparations']=sorted(a,key=lambda r:r['prepare_wall_ns'],reverse=True)[:6]
 groups.append(summary)
out=dict(result='PASS_VALID_BOUNDED_HUD_COUNTERS',records=len(rows),groups=groups,scope='Captured thread cycles and wall nanoseconds separately. CPU time100ns counters quantize to15.625ms in this environment; aggregate sums/zero individual samples do not prove precise scheduling gaps. Cycles not converted to milliseconds without frequency calibration. Diagnostic build overhead/livecadence not certified.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out))
