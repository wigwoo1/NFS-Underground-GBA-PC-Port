import sys,json,statistics
from pathlib import Path
from test_scene_process_transport import digest
import owned_sampled_road_sequence as sequence
from owned_camera_clip_transaction import clipped_camera_road
reference=sequence.clipped_camera_road;rows=[]
for report in ('work/camera/prototype-runs/owned-native-1791351241812904600.json','work/camera/prototype-runs/owned-native-1791352541751468500.json'):
 sys.argv=['oracle',report,'0','unused'];ns={};exec(compile(Path('work/camera/capture_fullscene_sample_oracle.py').read_text().split('import time,hashlib')[0],'fixed-setup','exec'),ns)
 timings={'reference':[],'native':[]};checks=0
 try:
  ns['prepared'].sample(.5)
  for i in range(60):
   outputs=[]
   order=[('reference',reference),('native',clipped_camera_road)]
   if i%2:order.reverse()
   for name,fn in order:
    sequence.clipped_camera_road=fn;value=ns['prepared'].sample(.5);outputs.append(digest(value));stage=next(s for s in ns['prepared'].pair._last_sample_stages if s['name']=='sampled_roads');timings[name].append(stage['wall_ns'])
   assert outputs[0]==outputs[1];checks+=1
 finally:sequence.clipped_camera_road=reference;ns['prepared'].close();ns['history'].close()
 rows.append(dict(report=report,exact_pairs=checks,medians_ns={k:statistics.median(v) for k,v in timings.items()},timings_ns=timings))
Path('work/camera/prototype-runs/native-clip-benchmark.json').write_text(json.dumps(dict(intervals=rows,scope='Alternating same captured full assemblies; road phase wall timing; no live speedup proof'),indent=2));print([(r['exact_pairs'],r['medians_ns']) for r in rows])
