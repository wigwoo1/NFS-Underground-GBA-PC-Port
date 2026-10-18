"""Verify the requested presentation phase using actual host timestamps."""
from pathlib import Path
import csv,json,statistics,sys
p=Path('work/camera');phase_us=int(sys.argv[1]);assert 0<phase_us<=15000
rows=[r for r in csv.DictReader((p/'road-attribute-live-parity.csv').open()) if int(r['ready'])]
lateness=[(int(r['swap_end_ns'])-int(r['deadline_ns'])-phase_us*1000)/1e6 for r in rows]
assert rows and all(v>=0 for v in lateness), 'Swap completed before requested phase'
interval=[(int(b['swap_end_ns'])-int(a['swap_end_ns']))/1e6 for a,b in zip(rows,rows[1:])]
def stats(v):return dict(median=statistics.median(v),p95=sorted(v)[int(.95*len(v))],maximum=max(v))
worst=sorted(zip(lateness,rows),key=lambda x:x[0],reverse=True)[:10]
outliers=[dict(display=int(r['display_index']),phase_lateness_ms=late,
               poll_lateness_ms=(int(r['poll_ns'])-int(r['deadline_ns']))/1e6,
               simulation_ms=(int(r['simulation_end_ns'])-int(r['simulation_start_ns']))/1e6,
               native_generation_ms=int(r['paired_prepare_ns'])/1e6,
               render_completion_lateness_ms=(int(r['render_end_ns'])-int(r['deadline_ns'])-phase_us*1000)/1e6) for late,r in worst]
report=dict(result='PASS',phase_us=phase_us,ready_frames=len(rows),phase_completion_lateness_ms=stats(lateness),over_1ms_late=sum(v>1 for v in lateness),ready_swap_interval_ms=stats(interval),worst=outliers,scope='Actual swap-return phase timing; GPU/display scanout and input latency are not measured. Original game state parity checked separately.')
(p/'presentation-phase-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
