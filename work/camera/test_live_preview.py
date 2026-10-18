from pathlib import Path
import csv,json,statistics
from scene_batches import batches
root=Path('work/camera');scenes=list(batches(root/'world.bin'));rows=list(csv.DictReader((root/'live-preview-timing.csv').open()))
assert len(rows)==180
rendered=[]
for i,row in enumerate(rows):
 now=int(row['refresh']);target=now-5
 if i:assert now==int(rows[i-1]['refresh'])+1
 available=[s for s in scenes if s['end_refresh']<=now]
 ready=bool(available and available[0]['end_refresh']<=target<=available[-1]['end_refresh'])
 assert int(row['rendered'])==int(ready),(now,ready)
 if not ready:continue
 older=max((s for s in available if s['end_refresh']<=target),key=lambda s:s['serial'])
 newer=next((s for s in available if s['serial']==older['serial']+1),older)
 alpha=0 if older==newer else (target-older['end_refresh'])/(newer['end_refresh']-older['end_refresh'])
 assert int(row['older'])==older['serial'] and int(row['newer'])==newer['serial'] and abs(float(row['alpha'])-alpha)<1e-8
 rendered.append(row)
assert len(rendered)==171
def summary(name):
 values=[float(r[name]) for r in rendered[1:]];ordered=sorted(values)
 return {'samples':len(values),'mean_ms':statistics.mean(values),'p95_ms':ordered[int(.95*(len(values)-1))],'max_ms':max(values),'over_16_667_ms':sum(x>1000/60 for x in values)}
report={'result':'PASS','source_scenes':48,'live_rendered_samples':len(rendered),'all_timeline_pairs_verified':True,'cold_first_total_ms':float(rendered[0]['total_ms']),'warm_simulation_and_capture':summary('simulation_capture_ms'),'warm_render':summary('render_ms'),'warm_combined':summary('total_ms'),'scope':'Unpaced live emulation, native capture, retained-memory handoff and offscreen 4K GPU completion. Excludes real display pacing, audio output and controller/input latency. Five-refresh presentation delay retained.'}
(root/'live-preview-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
