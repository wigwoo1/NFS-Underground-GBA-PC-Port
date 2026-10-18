import runpy,time,statistics
from pathlib import Path
from owned_closed_scene_memory import ClosedSceneMemory
v=runpy.run_path('work/camera/audit_failed_world_motion.py');namespace={};exec(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/scene-memory-merge-20261006/memory-before.py').read_text(),namespace);Old=namespace['ClosedSceneMemory'];times={Old:[],ClosedSceneMemory:[]}
for iteration in range(10):
 for cls in ((Old,ClosedSceneMemory) if iteration%2==0 else (ClosedSceneMemory,Old)):
  start=time.perf_counter_ns();maps=[cls(s.graph,v['rom']) for s in v['scenes']];times[cls].append(time.perf_counter_ns()-start)
  if cls is Old:original=maps
  else:updated=maps
 for a,b in zip(original,updated):
  assert dict(a.owned)==dict(b.owned) and a._owned_addresses==b._owned_addresses
  for address in a._owned_addresses[::101]:assert a.read(address,1)==b.read(address,1)
import json
result=dict(result='PASS_EXACT_MAPS_AND_READS',before_median_ms=statistics.median(times[Old])/1e6,after_median_ms=statistics.median(times[ClosedSceneMemory])/1e6,scope='Two captured scene maps,10 interleaved rounds; merge-only comparison,not live cadence')
Path('work/camera/scene-memory-merge-benchmark.json').write_text(json.dumps(result,indent=2));print(result)

import struct
from types import SimpleNamespace
g=v['scenes'][0].graph.graph;context=bytearray(g.context);struct.pack_into('<I',context,80,struct.unpack_from('<I',context,84)[0]);bad=SimpleNamespace(graph=SimpleNamespace(context=bytes(context),geometry=g.geometry,offsets=g.offsets,materials=g.materials,faces=g.faces))
for cls in (Old,ClosedSceneMemory):
 try:cls(bad,v['rom'])
 except ValueError as error:assert 'Conflicting owned scene memory' in str(error)
 else:raise AssertionError('Conflicting scene overlap accepted')
print('PASS original and optimized overlap conflict rejection')

import random
rng=random.Random(603011);checks=0
for a,b in zip(original,updated):
 for repeat in range(500):
  address=rng.choice(a._owned_addresses)+rng.randrange(-16,17);size=rng.randrange(0,96);values=[]
  for memory in (a,b):
   try:values.append(('ok',memory.read(address,size)))
   except ValueError as error:values.append(('error',str(error),memory.missing[-1] if memory.missing else None))
  assert values[0]==values[1];checks+=1
print('PASS',checks,'random boundary reads including missing ownership errors')
