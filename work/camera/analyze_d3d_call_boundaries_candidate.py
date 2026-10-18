import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());api=r['bounded_diagnostic_stats']['whole_run_api_intervals'];ledger=api['long_intervals'];assert ledger['dropped']==0 and ledger['total']==api['over_33_333ms']==len(ledger['records'])
expected=('nf_d3d_material_packet_cached','nf_d3d_world_batch','nf_d3d_source_hud_batch')
def analyze(rows):
 groups={name:[] for name in expected}
 for row in rows:
  assert row is not None and tuple(x['call'] for x in row)==expected
  for prof in row:
   a,b,c,d=[prof[k] for k in ('caller_begin_ns','native_begin_ns','native_end_ns','caller_end_ns')];assert a<=b<=c<=d and prof['native_cycles']>=0
   groups[prof['call']].append(dict(caller_ms=(d-a)/1e6,native_ms=(c-b)/1e6,before_ms=(b-a)/1e6,after_ms=(d-c)/1e6,cycles=prof['native_cycles']))
 return {name:dict(count=len(rows),median={k:statistics.median(x[k] for x in rows) for k in rows[0]} if rows else {},max={k:max(x[k] for x in rows) for k in rows[0]} if rows else {}) for name,rows in groups.items()}
out=dict(result='D3D_NATIVE_CALL_BOUNDARIES_RECONCILED',retained_last_window=analyze([(x.get('prepared') or {}).get('d3d_call_profiles') for x in r['presentation_samples']]),complete_long_intervals=analyze([x.get('d3d_call_profiles') for x in ledger['records']]),scope='Native D3D submission wall time including driver/scheduling, not GPU execution or physical presentation timing. Before/after native intervals include FFI/GIL/scheduling/profiling; no exclusive cause claim. Complete bounded long ledger and retained120 window separately.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out)
