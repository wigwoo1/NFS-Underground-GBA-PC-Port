import runpy,time,statistics
from pathlib import Path
from owned_complete_supplemental_sources import complete_wall_sources,_supplemental_cache_local
v=runpy.run_path('work/camera/profile_world_construction.py');ns={};exec(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/supplemental-source-cache-20261006/before.py').read_text(),ns);before=ns['complete_wall_sources'];timings={before:[],complete_wall_sources:[]}
for iteration in range(10):
 for scene in v['v']['scenes']:
  outputs={}
  for fn in ((before,complete_wall_sources) if iteration%2==0 else (complete_wall_sources,before)):
   started=time.perf_counter_ns();outputs[fn]=fn(scene.graph,scene.supplements,v['v']['rom']);timings[fn].append(time.perf_counter_ns()-started)
  assert outputs[before]==outputs[complete_wall_sources]
  assert complete_wall_sources(scene.graph,scene.supplements,v['v']['rom']) is outputs[complete_wall_sources]
try:complete_wall_sources(v['v']['scenes'][0].graph,v['v']['scenes'][1].supplements,v['v']['rom'])
except ValueError:pass
else:raise AssertionError('Unpaired publication accepted')
assert len(_supplemental_cache_local.entries)<=4
print('PASS exact supplemental geometry/material parity and publication rejection; warmedmedianms',*[round(statistics.median(timings[f])/1e6,3) for f in (before,complete_wall_sources)])
