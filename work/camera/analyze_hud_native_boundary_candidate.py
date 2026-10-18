"""Separate native HUD elapsed from observed Python boundary overhead."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals'];assert ledger['dropped']==0
rows=[]
for gap in ledger['records']:
 lease=gap['hud_lease_stages'];profile=lease.get('native_callback_profile')
 if profile is None:continue
 a,b,cycles=profile;begin=lease['callback_begin_ns'];end=lease['callback_end_ns'];assert begin<=a<=b<=end and cycles>=0
 row=dict(display_index=gap['display_index'],interval_ms=gap['interval_ns']/1e6,callback_ms=(end-begin)/1e6,native_callback_ms=(b-a)/1e6,before_native_ms=(a-begin)/1e6,after_native_ms=(end-b)/1e6,native_cycles=cycles)
 create=lease.get('native_create_profile')
 if create:
  a,b,cycles=create;assert a<=b<=lease['snapshot_end_ns'];row.update(native_create_ms=(b-a)/1e6,create_inside_snapshot=a>=lease['snapshot_begin_ns'])
 rows.append(row)
out=dict(result='PASS_NATIVE_HUD_BOUNDARY_CLOCKS',complete_long_intervals=ledger['total'],profiled_long_intervals=len(rows),rows=rows,scope='Elapsed boundary partitions include scheduling; after-native delay may include GIL reacquisition but is not exclusive GIL proof. Snapshot creation may predate take due to prefetch. Profiling can perturb timing; no visible60 qualification.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
