"""Attribute all recorded original updates to their presentation intervals."""
import csv,json,sys
from pathlib import Path

manifest=Path(sys.argv[1]);session=json.loads(manifest.read_text())
assert session['status']=='HOST_COMPLETE' and session['exit_code']==0
inputs=list(csv.DictReader(Path(session['input_trace']).open()))
displays=list(csv.DictReader(Path(session['display_trace']).open()))
stages=['live_capture','layer_capture','original_scanline']
cursor=0;intervals=[]
for previous,row in zip([None]+displays[:-1],displays):
 end=int(row['original_steps_total']);assert cursor<=end<=len(inputs)
 batch=inputs[cursor:end]
 assert len(batch)==int(row['original_steps_since_display'])
 times={key:sum(int(r[key+'_ns']) for r in batch) for key in stages}
 frame_ns=sum(int(r['end_ns'])-int(r['start_ns']) for r in batch)
 assert sum(times.values())<=frame_ns<=int(row['simulation_since_display_ns'])
 times['other_frame_work']=frame_ns-sum(times.values())
 times['batch_overhead']=int(row['simulation_since_display_ns'])-frame_ns
 assert sum(times.values())==int(row['simulation_since_display_ns'])
 for i,r in enumerate(batch,cursor):assert int(r['index'])==i
 intervals.append(dict(display=int(row['display_index']),original_steps=len(batch),due_poll_steps=int(row['display_simulation_steps']),swap_interval_ms=None if previous is None else (int(row['swap_end_ns'])-int(previous['swap_end_ns']))/1e6,original_work_ms={k:v/1e6 for k,v in times.items()},early_cpu_ms=int(row['early_generation_since_display_ns'])/1e6,early_gpu_ms=int(row['early_gpu_since_display_ns'])/1e6,due_render_ms=(int(row['render_end_ns'])-int(row['render_start_ns']))/1e6))
 cursor=end
report=dict(result='PASS',refreshes=len(inputs),display_intervals=len(intervals),assigned_original_updates=cursor,terminal_original_updates=len(inputs)-cursor,stage_total_ms={k:sum(r['original_work_ms'][k] for r in intervals) for k in intervals[0]['original_work_ms']},worst_intervals=sorted(intervals[1:],key=lambda r:r['swap_interval_ms'],reverse=True)[:12],scope='All original update hook times reconciled to cumulative presentation ledgers. Stage wall times include profiling overhead/preemption; scheduling, early work and rendering may occupy different parts of an interval. These values do not establish exclusive causality, physical latency or smooth60fps.')
output=manifest.with_name(manifest.stem+'-profile-intervals.json')
output.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
