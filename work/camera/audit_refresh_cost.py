"""Audit original refresh work and scene publication without inferring CPU/GPU causes."""
import csv,json,statistics,sys
from pathlib import Path
p=Path('work/camera')
trace=list(csv.DictReader((p/sys.argv[1]).open()))
frames=list(csv.DictReader((p/sys.argv[2]).open()))
assert trace and frames
samples=[]
for i,r in enumerate(trace):
 assert int(r['index'])==i and int(r['after'])==int(r['before'])+1
 if i:assert int(r['before'])==int(trace[i-1]['after']) and int(r['start_ns'])>=int(trace[i-1]['end_ns'])
 assert int(r['end_ns'])>=int(r['start_ns']) and int(r['scenes_after'])>=int(r['scenes_before'])
 samples.append(dict(refresh=int(r['after']),start=int(r['start_ns']),end=int(r['end_ns']),ms=(int(r['end_ns'])-int(r['start_ns']))/1e6,closed=int(r['scenes_after'])-int(r['scenes_before']),batch=int(r['batch']),present=int(r['present'])))
def stats(v):
 return dict(count=len(v),median_ms=statistics.median(v),p95_ms=sorted(v)[int(.95*len(v))],maximum_ms=max(v)) if v else dict(count=0)
misses=[]
for i,r in enumerate(frames):
 if not int(r['skipped']):continue
 prior=frames[i-1] if i else None
 item=dict(display=int(r['display_index']),skipped=int(r['skipped']),poll_late_ms=(int(r['poll_ns'])-int(r['deadline_ns']))/1e6)
 if prior:
  item.update(prior_display=int(prior['display_index']),prior_work_ms=(int(prior['swap_end_ns'])-int(prior['simulation_start_ns']))/1e6,prior_simulation_ms=(int(prior['simulation_end_ns'])-int(prior['simulation_start_ns']))/1e6,prior_pair_ms=int(prior['paired_prepare_ns'])/1e6)
  between=[s for s in samples if s['start']>=int(prior['swap_end_ns']) and s['end']<=int(r['poll_ns'])]
  item.update(intervening_original_refreshes=len(between),intervening_refresh_ms=sum(s['ms'] for s in between),intervening_closed_scenes=sum(s['closed'] for s in between))
 misses.append(item)
report=dict(result='PASS',refreshes=len(samples),all_original_refreshes_contiguous=True,total_closed_scenes=sum(s['closed'] for s in samples),scene_closing_refresh=stats([s['ms'] for s in samples if s['closed']]),no_scene_closing_refresh=stats([s['ms'] for s in samples if not s['closed']]),catchup_refresh=stats([s['ms'] for s in samples if s['batch']>1]),normal_batch_refresh=stats([s['ms'] for s in samples if s['batch']==1]),miss_events=len(misses),skipped_deadlines=sum(m['skipped'] for m in misses),misses=misses,scope='Recorded wall-clock frame execution and scene publication correlation; does not distinguish game execution, capture callbacks, scheduler stalls or physical scanout.')
if 'live_capture_ns' in trace[0] and any(int(r['live_capture_calls']) for r in trace):
 profile={}
 for name in ('live_capture','layer_capture','original_scanline'):
  values=[int(r[name+'_ns'])/1e6 for r in trace]
  for r,v,sample in zip(trace,values,samples):assert 0<=v<=sample['ms'],(name,r['index'],v,sample['ms'])
  profile[name]=dict(**stats(values),total_ms=sum(values),calls=sum(int(r[name+'_calls']) for r in trace))
 measured=[sum(int(r[name+'_ns']) for name in ('live_capture','layer_capture','original_scanline'))/1e6 for r in trace]
 for x,sample in zip(measured,samples):assert x<=sample['ms']+.000001
 report['profile']=profile
 report['unmeasured_frame_ms']=stats([sample['ms']-x for sample,x in zip(samples,measured)])
 report['profile_scope']='Selected event callbacks, layer capture and original scanline wall-clock only; residual includes emulation, other hooks, scene overlay work, scheduler and profiler overhead. Event gates and completed-scene sink are not covered.'
(p/sys.argv[3]).write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='misses'},indent=2))
