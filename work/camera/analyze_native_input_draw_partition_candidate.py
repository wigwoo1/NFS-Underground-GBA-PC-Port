"""Partition retained long API gaps using native input/draw callback clocks."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals'];assert ledger['dropped']==0 and len(ledger['records'])==ledger['total'];rows=[]
for gap in ledger['records']:
 lease=gap['hud_lease_stages'];outer=lease['native_callback_profile'];draw=lease['native_draw_boundaries']
 assert len(draw)==4 and outer[0]<=draw[0]<=draw[1]<=draw[2]<=draw[3]<=outer[1]
 before=draw[0]-outer[0];poll=draw[1]-draw[0];body=draw[2]-draw[1];finish=draw[3]-draw[2];after=outer[1]-draw[3]
 assert before+poll+body+finish+after==outer[1]-outer[0]
 stages=lease['source_packet_stages'];assert len(stages)==3 and all(x>=0 for x in stages)
 assert sum(stages)<=body
 rows.append(dict(index=gap['display_index'],api_interval_ms=gap['interval_ns']/1e6,native_total_ms=(outer[1]-outer[0])/1e6,before_draw_callback_ms=before/1e6,input_poll_ms=poll/1e6,draw_body_ms=body/1e6,callback_finish_ms=finish/1e6,after_draw_callback_ms=after/1e6,background_ms=stages[0]/1e6,world_geometry_ms=stages[1]/1e6,hud_ms=stages[2]/1e6,draw_body_other_ms=(body-sum(stages))/1e6,native_thread_cycles=outer[2]))
out=dict(result='PASS_COMPLETE_NATIVE_INPUT_DRAW_PARTITION',count=len(rows),rows=sorted(rows,key=lambda x:x['api_interval_ms'],reverse=True),scope='Complete retained long intervals; absolute native clocks nested in leased callback. Durations include locks and scheduling; not exclusive CPU or scanout proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
