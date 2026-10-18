from pathlib import Path
import json,time,statistics
from owned_closed_scene_memory import ClosedSceneMemory
from owned_complete_road_candidates import road_candidates as baseline
from owned_resolved_road_material_candidate import road_candidates as candidate
ns={};exec(Path('work/camera/test_progressive_source_samples_candidate.py').read_text(),ns);env=ns['env'];rom=env['rom'];scenes=env['scenes'];memories=[ClosedSceneMemory(s.graph,rom) for s in scenes];times=[[],[]];counts=[]
for iteration in range(128):
 for index in (iteration%2,1-iteration%2):
  begin=time.perf_counter_ns();rows=[(baseline,candidate)[index](s.graph,m) for s,m in zip(scenes,memories)];times[index].append(time.perf_counter_ns()-begin)
  if index==0:expected=rows
  else:actual=rows
 assert expected==actual
 if iteration==0:counts=[dict(candidates=len(r),unique_materials=len(set(x.material_index for x in r))) for r in rows]
validation=[]
class RejectTextures:
 def __init__(self,memory):self.memory=memory;self.failures=0
 def read(self,address,size):
  if size!=20:self.failures+=1;raise ValueError('Injected missing texture')
  return self.memory.read(address,size)
for scene,memory in zip(scenes,memories):
 readers=[RejectTextures(memory),RejectTextures(memory)]
 a=baseline(scene.graph,readers[0]);b=candidate(scene.graph,readers[1]);assert a==b and readers[0].failures==readers[1].failures
 validation.append(dict(case='missing_texture',exact_candidates=True,failed_reads=readers[0].failures))
from types import SimpleNamespace
import struct
closed=scenes[0].graph;g=closed.graph;raw=bytearray(g.materials);target=expected[0][0].material_index;at=0;found=False
while at<len(raw):
 h=struct.unpack_from('<12I',raw,at)
 if h[3]==target:struct.pack_into('<H',raw,at+98,0);found=True;break
 at+=120+(h[8] if h[9]==1 else 0)
assert found
modified=SimpleNamespace(graph=SimpleNamespace(context=g.context,materials=bytes(raw),geometry=g.geometry,offsets=g.offsets))
for function in (baseline,candidate):
 try:function(modified,memories[0]);raise AssertionError('Invalid texture dimensions accepted')
 except ValueError as error:assert str(error)=='Invalid road texture dimensions'
validation.append(dict(case='invalid_texture_height',both_reject=True))
out=dict(result='PASS_EXACT_RESOLVED_ROAD_MATERIAL',validation=validation,pairs=128,endpoints=counts,baseline=dict(median_ms=statistics.median(times[0])/1e6,mean_ms=statistics.mean(times[0])/1e6),candidate=dict(median_ms=statistics.median(times[1])/1e6,mean_ms=statistics.mean(times[1])/1e6),scope='Per-call successful immutable material texture resolution reused. All RoadCandidate fields exact on two complete actual endpoints. Candidate isolated; no native or live cadence proof.')
Path('outputs/nfsug-native-renderer/camera-research/resolved-road-material-20261009.json').write_text(json.dumps(out,indent=2));print(out)
