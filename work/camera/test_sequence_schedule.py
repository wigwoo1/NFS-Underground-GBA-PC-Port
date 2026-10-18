from pathlib import Path
import csv,json,bisect,statistics
from scene_batches import batches
root=Path('work/camera');times=[s['end_refresh'] for s in batches(root/'world.bin')]
rows=list(csv.DictReader((root/'sequence-render.csv').open()));assert len(rows)==times[-1]-times[0]-4
for index,row in enumerate(rows):
 now=int(row['refresh']);target=float(row['target']);older=int(row['older']);newer=int(row['newer']);alpha=float(row['alpha'])
 assert now==times[0]+5+index and target==now-5
 expected=bisect.bisect_right(times,target)-1;assert older==expected
 assert newer==min(older+1,len(times)-1)
 assert abs(times[older]*(1-alpha)+times[newer]*alpha-target)<1e-6
costs=[float(row['render_ms']) for row in rows];warm=costs[1:];ordered=sorted(warm)
report={'result':'PASS','source_scenes':len(times),'display_samples':len(rows),'startup_render_ms':costs[0],'subsequent_mean_ms':statistics.mean(warm),'subsequent_p95_ms':ordered[int(.95*(len(ordered)-1))],'subsequent_max_ms':max(warm),'subsequent_over_16_667_ms':sum(v>1000/60 for v in warm),'scope':'Prerecorded sequence, exact timeline checks and offscreen rendering. Disk packet reads, display scheduling, live emulation/capture and input latency are excluded from render timings.'}
(root/'sequence-schedule-tests.json').write_text(json.dumps(report,indent=2));print(report)
