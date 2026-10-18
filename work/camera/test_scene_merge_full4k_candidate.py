import sys,struct
from types import SimpleNamespace
from pathlib import Path
from owned_closed_scene_memory import ClosedSceneMemory as Baseline
from owned_closed_scene_merge_candidate import ClosedSceneMemory as Candidate
for shift,conflict in [(0,False),(16,False),(0,True),(16,True)]:
 context=bytearray(368);struct.pack_into('<I',context,84,100);struct.pack_into('<I',context,80,100+shift)
 context[304:368]=bytes([0])*64
 if conflict:context[304]=1
 graph=SimpleNamespace(context=bytes(context),geometry=b'',offsets=b'',materials=b'',faces=b'');closed=SimpleNamespace(graph=graph)
 outcomes=[]
 for cls in (Baseline,Candidate):
  try:outcomes.append(cls(closed,b'')._ranges)
  except ValueError:outcomes.append('conflict')
 assert outcomes[0]==outcomes[1] and (outcomes[0]=='conflict')==conflict
import owned_closed_scene_memory as memory
memory.ClosedSceneMemory=Candidate
sys.argv=['fixture','work/camera/prototype-runs/owned-native-1791434872973979000.json','work/camera/prototype-runs/scene-merge-full4k-parity.json']
source=Path('work/camera/test_owned_native_source_backdrop_batch_parity_candidate.py').read_text()
line=next(x for x in source.splitlines() if x.startswith('reference=json.loads'))
source=source.replace(line,"reference=json.loads(Path('work/camera/prototype-runs/scene-merge-current-baseline.json').read_text());assert [x['native_rgb_sha256'] for x in results]==[x['native_rgb_sha256'] for x in reference['frames']]")
exec(compile(source,'scene-merge-full4k-fixture','exec'))
