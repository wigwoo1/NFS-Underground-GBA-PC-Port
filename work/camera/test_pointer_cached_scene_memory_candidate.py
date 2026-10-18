from pathlib import Path
import json,time,statistics
from owned_closed_scene_memory import ClosedSceneMemory
from owned_pointer_cached_scene_memory_candidate import PointerCachedSceneMemory
ns={};exec(Path('work/camera/test_progressive_source_samples_candidate.py').read_text(),ns);env=ns['env'];rom=env['rom'];scenes=env['scenes'];times=[[],[]];counts=[]
for iteration in range(256):
 for index in (iteration%2,1-iteration%2):
  cls=(ClosedSceneMemory,PointerCachedSceneMemory)[index];begin=time.perf_counter_ns();memories=[cls(scene.graph,rom) for scene in scenes];times[index].append(time.perf_counter_ns()-begin)
  if index==0:baseline=memories
  else:candidate=memories
 if iteration==0:
  for a,b in zip(baseline,candidate):
   assert a._ranges==b._ranges and a._starts==b._starts and a.owned_byte_count==b.owned_byte_count
   for address,data in a._ranges:
    assert a.read(address,len(data))==b.read(address,len(data))==data
   counts.append(dict(merged_ranges=len(b._ranges),owned_bytes=b.owned_byte_count))
from types import SimpleNamespace
import struct
validation=[]
for kind in ('overlap_conflict','truncated_material'):
 context=bytearray(368);struct.pack_into('<I',context,84,0x02000100);struct.pack_into('<I',context,80,0x02000108)
 context[256:304]=bytes(range(48));context[304:368]=b'\xff'*64
 if kind=='truncated_material':struct.pack_into('<I',context,80,0x02000200)
 graph=SimpleNamespace(context=bytes(context),geometry=b'',offsets=b'',materials=b'\0'*47 if kind=='truncated_material' else b'',faces=b'',refresh=1)
 fixture=SimpleNamespace(graph=graph);errors=[]
 for cls in (ClosedSceneMemory,PointerCachedSceneMemory):
  try:cls(fixture,b'');raise AssertionError('Invalid fixture accepted')
  except (ValueError,struct.error) as error:errors.append(type(error).__name__)
 assert errors[0]==errors[1],errors
 validation.append(dict(case=kind,error=errors[0]))
summary=[dict(median_ms=statistics.median(v)/1e6,mean_ms=statistics.mean(v)/1e6) for v in times]
out=dict(result='PASS_EXACT_POINTER_CACHED_MEMORY',validation=validation,endpoint_counts=counts,baseline=summary[0],candidate=summary[1],pairs=256,scope='Controlled alternating actual two source endpoints, all sparse ranges and contained reads exact. Candidate not installed; no live performance claim.')
Path('outputs/nfsug-native-renderer/camera-research/pointer-cached-scene-memory-20261009.json').write_text(json.dumps(out,indent=2));print(out)
