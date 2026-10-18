import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals'];assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
labels=['validation','target_copy','plane0_copy','plane0_texture','plane1_copy','plane1_texture','plane2_copy','plane2_texture','records_copy','hud_draw']
def phases(e):
 p=e['prepared'];v=p['hud_phase_cycles'];s=next(x for x in p['consumer_stages'] if x['stage']=='ordered_sky_world_hud');t=s['native_hud_ticks'];assert len(v)==12 and len(t)==12 and t[0]>0;assert v[1:]==sorted(v[1:]) and t[1:]==sorted(t[1:]);assert v[1]>0
 result=[dict(name=k,wall_ms=(t[i+1]-t[i])/t[0]*1000,cycles=v[i+1]-v[i]) for i,k in enumerate(labels,1)]
 assert abs(sum(x['wall_ms'] for x in result)-(t[-1]-t[1])/t[0]*1000)<.000001
 return result
recent=[x for e in r['presentation_samples'] for x in phases(e)];reference={k:dict(wall_median_ms=statistics.median(x['wall_ms'] for x in recent if x['name']==k),cycles_median=statistics.median(x['cycles'] for x in recent if x['name']==k)) for k in labels}
rows=[]
for e in ledger['records']:
 for x in phases(e):
  ref=reference[x['name']];rows.append(dict(identity=[e['epoch'],e['generation'],e['display_index']],interval_ms=e['interval_ns']/1e6,**x,wall_to_recent_median=None if ref['wall_median_ms']==0 else x['wall_ms']/ref['wall_median_ms'],cycles_to_recent_median=None if ref['cycles_median']==0 else x['cycles']/ref['cycles_median']))
out=dict(result='PASS_COMPLETE_LONG_HUD_WALL_CYCLES',raw=sys.argv[1],long_frames=ledger['total'],phase_rows=len(rows),native_intervals=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_intervals'],recent_reference=reference,largest_phases=sorted(rows,key=lambda x:x['wall_ms'],reverse=True)[:25],scope='Exact complete long-frame HUD phase ticks and same-owner cycles. Recent120frames reference is contextual, not matched workload or causal control. Cycles not converted to CPU duration; no exclusive scheduler/GPU/driver cause or60claim.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result'],out['long_frames']);print(out['native_intervals']);print(out['largest_phases'][:5])
