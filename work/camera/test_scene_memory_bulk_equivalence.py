import runpy,time,statistics
from pathlib import Path
from owned_closed_scene_memory import ClosedSceneMemory
v=runpy.run_path('work/camera/audit_failed_world_motion.py');namespace={};exec(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/scene-memory-bulk-insertion-20261006/before.py').read_text(),namespace);Old=namespace['ClosedSceneMemory'];times={Old:[],ClosedSceneMemory:[]}
for iteration in range(10):
 for cls in ((Old,ClosedSceneMemory) if iteration%2==0 else (ClosedSceneMemory,Old)):
  start=time.perf_counter_ns();maps=[cls(s.graph,v['rom']) for s in v['scenes']];times[cls].append(time.perf_counter_ns()-start)
  if cls is Old:original=maps
  else:updated=maps
 for a,b in zip(original,updated):
  assert dict(a.owned)==dict(b.owned) and a._owned_addresses==b._owned_addresses
  for address in a._owned_addresses[::101]:assert a.read(address,1)==b.read(address,1)
print('PASS exact scene byte maps, sorted addresses and read parity; interleaved median ms',*[round(statistics.median(times[c])/1e6,3) for c in (Old,ClosedSceneMemory)])

import struct
from types import SimpleNamespace
g=v['scenes'][0].graph.graph;context=bytearray(g.context);struct.pack_into('<I',context,80,struct.unpack_from('<I',context,84)[0]);bad=SimpleNamespace(graph=SimpleNamespace(context=bytes(context),geometry=g.geometry,offsets=g.offsets,materials=g.materials,faces=g.faces))
for cls in (Old,ClosedSceneMemory):
 try:cls(bad,v['rom'])
 except ValueError as error:assert 'Conflicting owned scene memory' in str(error)
 else:raise AssertionError('Conflicting scene overlap accepted')
print('PASS original and optimized overlap conflict rejection')
