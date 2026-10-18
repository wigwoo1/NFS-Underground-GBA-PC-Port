import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows=[]
ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals'];assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
for sample in ledger['records']:
 stages=sample['consumer_stages'];stage=next(s for s in stages if s['stage']=='ordered_sky_world_hud');t=stage['native_hud_ticks'];outer=stage['native_tail_ticks']
 assert len(t)==12 and t[0]>0 and t[0]==outer[0] and t[1]>=outer[5]
 if t[2]==0:
  assert all(v==0 for v in t[2:]);continue
 assert all(a<=b for a,b in zip(t[1:],t[2:])) and t[11]<=outer[6]
 names=['validation','target_copy','plane0_copy','plane0_upload','plane1_copy','plane1_upload','plane2_copy','plane2_upload','records_copy','draw']
 values={n+'_ms':(b-a)*1000/t[0] for n,a,b in zip(names,t[1:],t[2:])}
 assert abs(sum(values.values())-(t[11]-t[1])*1000/t[0])<1e-6
 rows.append(dict(display_index=sample['display_index'],**values))
out=dict(result='PASS_COMPLETE_LONG_HUD_PHASES',samples=len(rows),rows=rows,maxima={k:max(x[k] for x in rows) for k in (rows[0] if rows else {}) if k!='display_index'},scope='Every retained long API interval, zero dropped records; exact native containment, not exclusive driver/GPU cause or visible60 proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out))
