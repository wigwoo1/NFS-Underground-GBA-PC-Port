import sys,json,statistics
from pathlib import Path
import owned_sampled_world_frame as module
from owned_native_frame_join import join_frame
from test_scene_process_transport import digest
reference=module.join_frame;results=[]
for report in ('work/camera/prototype-runs/owned-native-1791351241812904600.json','work/camera/prototype-runs/owned-native-1791352541751468500.json'):
 sys.argv=['oracle',report,'0','unused'];ns={};exec(compile(Path('work/camera/capture_fullscene_sample_oracle.py').read_text().split('import time,hashlib')[0],'fixed-setup','exec'),ns)
 timings={'reference':[],'native':[]}
 try:
  ns['prepared'].sample(.5)
  for i in range(60):
   order=[('reference',reference),('native',join_frame)]
   if i%2:order.reverse()
   values=[]
   for name,fn in order:
    module.join_frame=fn;value=ns['prepared'].sample(.5);values.append(digest(value));timings[name].append(ns['prepared'].pair._last_sample_stages[-1]['wall_ns'])
   assert values[0]==values[1]
 finally:module.join_frame=reference;ns['prepared'].close();ns['history'].close()
 results.append(dict(report=report,exact_pairs=60,medians_ns={k:statistics.median(v) for k,v in timings.items()},timings_ns=timings))
Path('work/camera/prototype-runs/native-frame-join-benchmark.json').write_text(json.dumps(dict(intervals=results,scope='Alternating fixed full assembly encoding phase; no live contention proof'),indent=2));print([(x['medians_ns']) for x in results])
