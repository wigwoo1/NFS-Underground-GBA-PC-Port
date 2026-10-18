import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());stages={k:[] for k in ('buffer','state','draw_release','native_total','python_stage','outside_native')};checks=0;cycles=[]
for row in r['presentation_samples']:
 entries=(row.get('prepared') or {}).get('consumer_stages',[])
 profile=next((x for x in entries if x['stage']=='backdrop_native_profile'),None)
 if not profile:continue
 q=profile['stamps'];assert len(q)==9 and q[8]>0 and q[:4]==sorted(q[:4]) and q[4:8]==sorted(q[4:8])
 checks+=1
 for i,k in enumerate(('buffer','state','draw_release')):stages[k].append((q[i+1]-q[i])*1000/q[8])
 native=(q[3]-q[0])*1000/q[8];wall=next(x['elapsed_ns']/1e6 for x in entries if x['stage']=='backdrop_geometry')
 assert wall+0.01>=native
 stages['native_total'].append(native);stages['python_stage'].append(wall);stages['outside_native'].append(wall-native);cycles.append(q[7]-q[4])
def stats(v):
 v=sorted(v);return dict(count=len(v),median=statistics.median(v),p95=v[min(len(v)-1,int(len(v)*.95))],maximum=max(v))
assert checks>0
out=dict(result='PASS_NATIVE_BACKDROP_STAMPS',checks=checks,wall_ms={k:stats(v) for k,v in stages.items()},thread_cycles=stats(cycles),scope='CPU native submission wall time and execution cycles; outside-native includes Python preparation, preceding clear, profiling calls and scheduling. GPU completion and driver-wait causality not established.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
