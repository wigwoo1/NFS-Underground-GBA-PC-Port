"""Wall-clock game speed audit for complete pause histories."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());assert r['result']=='SMOKE_COMPLETE' and r['error'] is None
pauses=r['pause_events'];retention=r.get('pause_retention');assert retention is not None and retention['dropped_records']==0 and retention['total_records']==len(pauses);assert not r['quit_while_paused']
paused=0
for x in pauses:
 assert x['begin_ns']<=x['end_ns'];assert x['duration_ns']==x['end_ns']-x['begin_ns'];paused+=x['duration_ns']
t=r['timing'];assert t['original_clock_hz']==16777216 and t['cycles_per_update']==280896;active=t['live_elapsed_ns']-paused;sim=r['original_updates']*t['cycles_per_update']/t['original_clock_hz'];period=t['cycles_per_update']/t['original_clock_hz'];difference=sim-active/1e9
assert active>0 and abs(difference)<=2*period,(difference,period)
out=dict(result='PASS_ORIGINAL_SPEED_AGAINST_ACTIVE_WALL_CLOCK',updates=r['original_updates'],active_wall_seconds=active/1e9,paused_seconds=paused/1e9,simulated_seconds=sim,difference_ms=difference*1000,simulation_to_active_wall_ratio=sim/(active/1e9),tolerance_seconds=2*period,scope='Entire observed run with complete pause ledger; two-update tolerance for endpoint timing. Does not prove per-update cadence, gameplay fidelity or visible60fps.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))

