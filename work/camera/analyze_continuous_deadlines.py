"""Classify observed display skips without confusing next-row skip with its cause."""
from pathlib import Path
import csv,json,statistics,sys
p=Path('work/camera');display_path=Path(sys.argv[2]) if len(sys.argv)>2 else p/'road-attribute-live-parity.csv';rows=list(csv.DictReader(display_path.open()));ready=[r for r in rows if int(r['ready'])];assert ready
trace=list(csv.DictReader(Path(sys.argv[1]).open())) if len(sys.argv)>1 else []
trace_supplied=len(sys.argv)>1
if trace_supplied:
 assert trace, 'Empty original-refresh trace'
 for i,t in enumerate(trace):
  assert int(t['index'])==i and int(t['after'])==int(t['before'])+1
  assert int(t['end_ns'])>=int(t['start_ns'])
  if i:assert int(t['start_ns'])>=int(trace[i-1]['end_ns'])
 # A final original refresh can finish after the last presentation row.
 assert sum(int(t['end_ns'])<=int(rows[-1]['simulation_end_ns']) for t in trace)==int(rows[-1]['simulated']), 'Trace does not cover this display run'
 for row in rows:
  count=int(row['simulated'])
  assert count<=len(trace)
  if count:assert int(trace[count-1]['end_ns'])<=int(row['simulation_end_ns'])
  if count<len(trace):assert int(trace[count]['start_ns'])>=int(row['simulation_end_ns'])
def ns(row,key):return int(row[key])
def stages(row):
 values=dict(simulation=ns(row,'simulation_end_ns')-ns(row,'simulation_start_ns'),native_pair_generation=ns(row,'paired_prepare_ns'),renderer_asset_load=ns(row,'renderer_load_ns'),renderer_draw=ns(row,'renderer_draw_ns'),renderer_hud=ns(row,'renderer_hud_ns'),renderer_gpu_finish=ns(row,'renderer_finish_ns'),window_stage_swap=ns(row,'swap_end_ns')-ns(row,'render_end_ns'))
 # Includes validation, memory assembly, renderer setup and cleanup; not a
 # single function measurement. Paired generation precedes renderer marks.
 measured=sum(values[k] for k in ('native_pair_generation','renderer_asset_load','renderer_draw','renderer_hud','renderer_gpu_finish'))
 residual=ns(row,'render_end_ns')-ns(row,'render_start_ns')-measured
 assert residual>=0, 'Overlapping or inconsistent renderer timing'
 values['packet_setup_cleanup_residual']=residual
 return values
misses=[]
for previous,row in zip(rows,rows[1:]):
 skip=ns(row,'skipped');assert ns(row,'display_index')-ns(previous,'display_index')==1+skip
 if not skip:continue
 # Expected next deadline after previous display, exact integer ceil at60Hz.
 next_index=ns(previous,'display_index')+1;next_deadline=(next_index*1_000_000_000+59)//60
 until_poll=[t for t in trace if ns(t,'start_ns')>=ns(previous,'swap_end_ns') and ns(t,'end_ns')<=ns(row,'poll_ns')]
 durations=stages(previous);dominant=max(durations,key=durations.get)
 misses.append(dict(display=ns(row,'display_index'),skipped=skip,previous_display=ns(previous,'display_index'),previous_ready=bool(ns(previous,'ready')),previous_stages_ms={k:v/1e6 for k,v in durations.items()},previous_dominant_stage=dominant,previous_combined_ms=(ns(previous,'swap_end_ns')-ns(previous,'simulation_start_ns'))/1e6,previous_end_after_next_deadline_ms=(ns(previous,'swap_end_ns')-next_deadline)/1e6,poll_after_next_deadline_ms=(ns(row,'poll_ns')-next_deadline)/1e6,unlogged_refreshes_between=len(until_poll),unlogged_refresh_time_ms=sum(ns(t,'end_ns')-ns(t,'start_ns') for t in until_poll)/1e6))
summary={}
for stage in stages(ready[0]):
 values=[stages(r)[stage]/1e6 for r in ready];summary[stage]=dict(median=statistics.median(values),p95=sorted(values)[int(.95*len(values))],maximum=max(values))
slow=sorted(ready,key=lambda r:ns(r,'swap_end_ns')-ns(r,'simulation_start_ns'),reverse=True)[:12]
for event in misses:
 if not trace_supplied:
  event['unlogged_refreshes_between']=None;event['unlogged_refresh_time_ms']=None
refresh_stats={}
if trace_supplied:
 for label,subset in [('all',trace),('presentation_iteration',[t for t in trace if int(t['present'])]),('nonpresentation_iteration',[t for t in trace if not int(t['present'])])]:
  values=sorted((ns(t,'end_ns')-ns(t,'start_ns'))/1e6 for t in subset)
  refresh_stats[label]=dict(count=len(values),median=statistics.median(values) if values else None,p95=values[int(.95*len(values))] if values else None,maximum=max(values) if values else None,total_ms=sum(values))
report=dict(result='PASS',recorded_displays=len(rows),ready_displays=len(ready),skipped_displays=sum(ns(r,'skipped') for r in rows),miss_events=misses,stage_ms=summary,slowest=[dict(display=ns(r,'display_index'),combined_ms=(ns(r,'swap_end_ns')-ns(r,'simulation_start_ns'))/1e6,stages_ms={k:v/1e6 for k,v in stages(r).items()}) for r in slow],refresh_trace_records=len(trace),refresh_trace_supplied=trace_supplied,original_refresh_ms=refresh_stats,scope='Observed stage timing and prior-row attribution for missed displays. GPU draw is asynchronous; finish includes synchronization. Without refresh trace, time between display rows may include unlogged simulation; cannot classify it solely as scheduler sleep. Not smooth60fps proof.')
(p/'continuous-deadline-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(skips=report['skipped_displays'],events=len(misses),stage_ms=summary,scope=report['scope']),indent=2))
