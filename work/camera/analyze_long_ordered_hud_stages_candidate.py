import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());l=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals'];assert l['dropped']==0 and l['total']==len(l['records']);rows=[]
labels=['validation','target_copy','plane0_copy','plane0_texture','plane1_copy','plane1_texture','plane2_copy','plane2_texture','records_copy','hud_draw']
for e in l['records']:
 s=next(x for x in e['prepared']['consumer_stages'] if x['stage']=='ordered_sky_world_hud');t=s['native_tail_ticks'];h=s['native_hud_ticks'];assert len(t)==7 and len(h)==12;assert t[0]>0 and t[1:]==sorted(t[1:]);assert h[0]==t[0] and h[1:]==sorted(h[1:]);assert t[5]<=h[1]<=h[-1]<=t[6]
 scale=1000/t[0];parts={k:(b-a)*scale for k,a,b in zip(labels,h[1:],h[2:])};total=(h[-1]-h[1])*scale;assert abs(sum(parts.values())-total)<.000001
 rows.append(dict(identity=[e['epoch'],e['generation'],e['display_index']],sky_ms=(t[2]-t[1])*scale,world_ms=(t[4]-t[3])*scale,hud_ms=(t[6]-t[5])*scale,between_calls_ms=((t[3]-t[2])+(t[5]-t[4]))*scale,hud_parts_ms=parts))
out=dict(result='PASS_COMPLETE_LONG_ORDERED_HUD_STAGE_PARTITIONS',rows=rows,scope='Native source-derived tick labels and complete long-frame ledger. Copy spans include native execution, synchronization and scheduling; not exclusive memory-bandwidth cost or GPU duration.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result'],len(rows));print(sorted(rows,key=lambda x:x['hud_ms'],reverse=True)[:2])
