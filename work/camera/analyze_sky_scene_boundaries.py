"""Audit committed sky motion across scene-pair boundaries, not just inside pairs."""
import json,sys,math
from pathlib import Path
from analyze_live_sky_cadence import analyze
r=json.loads(Path(sys.argv[1]).read_text());base=analyze(r)
sources={(s['epoch'],s['publication']):s for s in r['sky_capture_records']}
rows=[]
for x in r['presentation_samples']:
 if not(x.get('interpolated') and x.get('hidden_window_presented')):continue
 a=sources[x['epoch'],x['source_older']]['angle'];b=sources[x['epoch'],x['refresh']]['angle'];delta=((b-a+8192)&16383)-8192
 angle=(b&16383) if x['alpha']==1 else (a&16383)+delta*x['alpha']
 rows.append(dict(index=x['display_index'],epoch=x['epoch'],older=x['source_older'],newer=x['refresh'],phase=(angle*240/4096)%240,delta=delta,alpha=x['alpha'],commit_ns=x['native_committed_sample'][6]))
transitions=[]
for a,b in zip(rows,rows[1:]):
 if a['epoch']!=b['epoch'] or (a['older'],a['newer'])==(b['older'],b['newer']):continue
 travel=((b['phase']-a['phase']+120)%240)-120
 transitions.append(dict(previous=a,current=b,travel_texels=travel,gap_ms=(b['commit_ns']-a['commit_ns'])/1e6,held_phase=math.isclose(travel,0,abs_tol=1e-10)))
out=dict(result='AUDITED',boundary_count=len(transitions),held_boundary_count=sum(x['held_phase'] for x in transitions),largest_boundary_travel=sorted(transitions,key=lambda x:abs(x['travel_texels']),reverse=True)[:12],within_pair_audit=base,scope='Actual committed requested sky phase at scene boundaries; magnitude is measured, not a correctness threshold. Does not verify rendered pixels or physical scanout.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k not in ('largest_boundary_travel','within_pair_audit')}))
