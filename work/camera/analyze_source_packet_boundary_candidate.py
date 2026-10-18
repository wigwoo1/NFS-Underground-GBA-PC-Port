"""Interpret leased native callback as whole source-packet generation, not HUD-only."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals'];assert ledger['dropped']==0
rows=[]
for gap in ledger['records']:
 lease=gap['hud_lease_stages'];a,b,cycles=lease['native_callback_profile'];assert lease['callback_begin_ns']<=a<=b<=lease['callback_end_ns']
 split=gap['hud_build_split'];assert len(split)==8 and all(type(x)is int and x>=0 for x in split)
 # HUD build total is recorded inside source packet generation. Other elapsed time is not exclusively geometry CPU.
 native=b-a;hud=split[7];assert hud<=native
 rows.append(dict(display_index=gap['display_index'],interval_ms=gap['interval_ns']/1e6,source_packet_callback_ms=native/1e6,hud_build_ms=hud/1e6,source_packet_other_elapsed_ms=(native-hud)/1e6,after_native_ms=(lease['callback_end_ns']-b)/1e6,native_thread_cycles=cycles))
out=dict(result='PASS_COMPLETE_SOURCE_PACKET_BOUNDARY_PARTITION',rows=sorted(rows,key=lambda x:x['interval_ms'],reverse=True),scope='Callback also validates source arrays, polls input, builds world geometry/materials, acquires/releases HUD leases. Other elapsed includes scheduling/lock waits; not exclusive geometry CPU or graphics-driver time. Context-free source builder suppresses legacy draw/upload commands.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
