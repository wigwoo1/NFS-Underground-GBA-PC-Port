import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals']
assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
rows=[]
for gap in ledger['records']:
 v=gap['native_present_ticks'];outer=gap['present_stage_ns']
 assert len(v)==6 and all(type(x) is int for x in v) and v[0]>0 and all(a<=b for a,b in zip(v[1:],v[2:]))
 assert outer['pumped']-1000<=v[1]*1e9/v[0]<=v[5]*1e9/v[0]<=outer['presented']+1000
 parts={name:(b-a)*1000/v[0] for name,a,b in zip(['get_buffer_ms','copy_resource_ms','release_ms','dxgi_present_ms'],v[1:],v[2:])}
 assert abs(sum(parts.values())-(v[5]-v[1])*1000/v[0])<1e-8
 rows.append(dict(index=gap['display_index'],interval_ms=gap['interval_ns']/1e6,**parts))
out=dict(result='PASS_COMPLETE_NATIVE_PRESENT_TICKS',rows=sorted(rows,key=lambda x:x['dxgi_present_ms'],reverse=True),long_intervals=len(rows),scope='Complete retained long API intervals zero drops, same-thread native QPC phases; elapsed includes scheduler and driver wait. No exclusive GPU cause or visible60fps proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
