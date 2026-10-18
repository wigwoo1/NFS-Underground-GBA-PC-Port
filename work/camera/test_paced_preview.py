from pathlib import Path
import csv,json,statistics,sys,re
from scene_batches import batches
prefix=sys.argv[1] if len(sys.argv)>1 else 'paced-preview'
root=Path('work/camera');rows=list(csv.DictReader((root/f'{prefix}-timing.csv').open()));scenes=list(batches(root/'world.bin'));base=8842
previous=-1;skips=rendered=0
for row in rows:
 poll=int(row['poll_ns']);tick=int(row['display_index']);sim=int(row['simulated']);now=int(row['refresh'])
 assert tick==poll*60//10**9 and sim==poll*16777216//(10**9*280896)
 assert now==base+sim and int(row['skipped'])==tick-previous-1
 assert int(row['deadline_ns'])==(tick*10**9+59)//60
 target=base+tick*16777216/(280896*60)-5;assert abs(float(row['target'])-target)<1e-8
 available=[s for s in scenes if s['end_refresh']<=now]
 ready=bool(available and available[0]['end_refresh']<=target<=available[-1]['end_refresh'])
 assert bool(int(row['ready']))==ready,(tick,target,now)
 if ready:
  older=max((s for s in available if s['end_refresh']<=target),key=lambda s:s['serial'])
  newer=next((s for s in available if s['serial']==older['serial']+1),older)
  alpha=0 if older==newer else (target-older['end_refresh'])/(newer['end_refresh']-older['end_refresh'])
  assert int(row['older'])==older['serial'] and int(row['newer'])==newer['serial'] and abs(float(row['alpha'])-alpha)<1e-8
  rendered+=1
 skips+=int(row['skipped']);previous=tick
assert previous==179
log=(root/f'{prefix}-log.txt').read_text();assert 'result=0' in log and 'simulated=179' in log
warm=[r for r in rows if int(r['display_index'])>=30 and r['ready']=='1']
lateness=[(int(r['render_end_ns'])-int(r['deadline_ns']))/1e6 for r in warm];ordered=sorted(lateness)
intervals=[(int(b['render_end_ns'])-int(a['render_end_ns']))/1e6 for a,b in zip(warm,warm[1:])]
if prefix=='paced-warm':assert skips==0 and rendered==169
report={'result':'PASS','setup_timing':'Context initialized before clock' if 'setup_ns=' in log else 'Cold context included in timed loop','scheduled_display_slots':180,'original_simulation_refreshes':179,'rendered':rendered,'unavailable':len(rows)-rendered,'skipped_display_slots':skips,'all_source_counts_and_pose_targets_verified':True,'warm_samples_after_half_second':len(warm),'warm_skipped_slots':sum(int(r['skipped']) for r in rows if int(r['display_index'])>=30),'warm_completion_lateness_ms':{'mean':statistics.mean(lateness),'p95':ordered[int(.95*(len(ordered)-1))],'max':max(lateness),'beyond_next_deadline':sum(v>1000/60 for v in lateness)},'warm_completion_interval_ms':{'mean':statistics.mean(intervals),'min':min(intervals),'max':max(intervals)},'scope':'Three-second real-time offscreen GPU scheduling; no SwapBuffers/display scanout, audio output or controller/input-latency measurement. See setup_timing for initialization scope; five-refresh delay retained.'}
if 'window_buffer=1' in log:
 assert int(re.search(r'swaps=(\d+)',log).group(1))==len(rows)
 swap_lateness=sorted((int(r['swap_end_ns'])-int(r['deadline_ns']))/1e6 for r in warm)
 report['successful_window_swaps']=len(rows)
 report['warm_swap_return_lateness_ms']={'mean':statistics.mean(swap_lateness),'p95':swap_lateness[int(.95*(len(swap_lateness)-1))],'max':max(swap_lateness)}
 report['scope']='Three-second paced hidden-window buffer swaps. Swap return is not proof of visible scanout or smooth displayed motion. Audio/input latency unmeasured; five-refresh delay retained.'
(root/f'{prefix}-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
