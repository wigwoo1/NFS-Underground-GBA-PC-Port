import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());api=r['bounded_diagnostic_stats']['whole_run_api_intervals'];ledger=api['long_intervals'];assert ledger['dropped']==0 and ledger['total']==api['over_33_333ms']==len(ledger['records'])
def analyze(rows):
 out=[]
 for prof in rows:
  assert prof is not None
  a,b,c,d=[prof[k] for k in ('caller_begin_ns','native_begin_ns','native_end_ns','caller_end_ns')];assert a<=b<=c<=d and prof['native_cycles']>=0
  out.append(dict(caller_ms=(d-a)/1e6,native_ms=(c-b)/1e6,before_native_ms=(b-a)/1e6,after_native_ms=(d-c)/1e6,native_cycles=prof['native_cycles']))
 return dict(count=len(out),median={k:statistics.median(x[k] for x in out) for k in out[0]} if out else {},max={k:max(x[k] for x in out) for k in out[0]} if out else {},rows=out)
out=dict(result='NATIVE_PACKET_CALL_BOUNDARIES_RECONCILED',retained_last_window=analyze([(x.get('prepared') or {}).get('bundle_transfer_profile') for x in r['presentation_samples']]),complete_long_intervals=analyze([x.get('bundle_transfer_profile') for x in ledger['records']]),scope='Direct native QPC boundaries inside Python perf-counter interval, all same Windows QPC clock. Before/after intervals include marshalling, lock reacquisition/scheduling and wrapper overhead; no exclusive GIL attribution or GPU/visible motion claim. Profiling overhead present.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print({k:{a:b for a,b in v.items() if a!='rows'} if isinstance(v,dict) else v for k,v in out.items()})
