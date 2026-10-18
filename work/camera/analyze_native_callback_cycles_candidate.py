import json,statistics,sys
from pathlib import Path
profile=json.loads(Path('work/camera/prototype-runs/native-callback-cycles-20261009.json').read_text());raw=json.loads(Path(sys.argv[1]).read_text());rows=profile['rows'];assert profile['dropped']==0
mapping={(x['epoch'],x['generation'],x['index']):x for x in rows};assert len(mapping)==len(rows)
for x in rows:
 t=x['native_stages'];assert t[0]<=t[1]<=t[2]<=t[3] and x['begin_ns']<=t[0]<=t[3]<=x['end_ns']
 assert 0<x['native_cycles']<=x['session_thread_cycles']
 x['native_ms']=(t[3]-t[0])/1e6;x['session_ms']=(x['end_ns']-x['begin_ns'])/1e6;x['outside_native_cycles']=x['session_thread_cycles']-x['native_cycles']
ledger=raw['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals'];assert ledger['dropped']==0 and len(ledger['records'])==ledger['total']
joined=[]
for l in ledger['records']:
 x=mapping[(l['epoch'],l['generation'],l['display_index'])];h=l['hud_lease_stages'];assert h['callback_begin_ns']<=x['native_begin_ns']<=x['native_end_ns']<=h['callback_end_ns']
 joined.append(dict(index=x['index'],native_ms=x['native_ms'],session_ms=x['session_ms'],native_cycles=x['native_cycles'],outside_native_cycles=x['outside_native_cycles'],callback_outside_native_ms=((h['callback_end_ns']-h['callback_begin_ns'])-(x['native_end_ns']-x['native_begin_ns']))/1e6))
result=dict(result='PASS_IDENTITY_JOINED_CALLBACK_CYCLES',captures=len(rows),long_intervals=len(joined),all_medians={k:statistics.median(x[k] for x in rows) for k in ('native_ms','session_ms','native_cycles','outside_native_cycles')},long_medians={k:statistics.median(x[k] for x in joined) for k in joined[0] if k!='index'} if joined else {},rows=joined,scope='Owner-thread cycles cover nested native draw callback and wholeprepare, residual includes D3D/backend/Python work. Callback wall residual includes wrappers/FFI/GIL/scheduling, not exclusive attribution; cycles not converted to fixed-frequency time. No60fps proof.')
Path('work/camera/prototype-runs/native-callback-cycles-summary-20261009.json').write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='rows'})
