import time,statistics,json
from pathlib import Path
from owned_geometry_tail_capability_candidate import GeometryTailOwners
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010')
ns={};exec(compile((cp/'owned_geometry_tail_capability_before_join.py').read_text(),'old_capability','exec'),ns)
folder=Path('work/camera/prototype-runs/child-scene-1791637661169682300');owners=tuple((folder/(name+'.frame.bin')).read_bytes() for name in ('older','newer'))
old=ns['GeometryTailOwners'](4,owners);new=GeometryTailOwners(4,owners);timings={False:[],True:[]}
try:
 for iteration in range(24):
  for enabled in ((False,True) if iteration%2==0 else (True,False)):
   capability=new if enabled else old;begin=time.perf_counter_ns();prefixes=tuple(capability.geometry(4,k) for k in range(2));frames=tuple(capability.restore(4,k,p) for k,p in enumerate(prefixes));end=time.perf_counter_ns()
   assert all(bytes(frame)==owners[k] for k,frame in enumerate(frames))
   assert prefixes==tuple(old.geometry(4,k) for k in range(2))
   timings[enabled].append((end-begin)/1e6)
finally:old.close();new.close()
assert all(bytes(frame)==owners[k] for k,frame in enumerate(frames))
out=dict(result='PASS_SINGLE_COPY_GEOMETRY_JOIN',rounds=24,median_ms={str(k):statistics.median(v) for k,v in timings.items()},exact_frames=True,retained_after_close=True,scope='Captured pair geometry pack+restore cost; excludes actual service, child preparation and live frame cadence.')
(cp/'geometry-single-copy-join.json').write_text(json.dumps(out,indent=2));print(out)
