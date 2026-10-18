import struct,random,json
from types import SimpleNamespace
from pathlib import Path
from owned_closed_scene_memory import ClosedSceneMemory as Baseline
from owned_closed_scene_merge_candidate import ClosedSceneMemory as Candidate
rng=random.Random(6149);cases=0;conflicts=0
for shift in range(-64,81):
 canonical=bytes(rng.randrange(256) for _ in range(256));base=0x02000100
 for bad in (False,True):
  context=bytearray(368);struct.pack_into('<I',context,84,base);struct.pack_into('<I',context,80,base+shift)
  context[256:304]=canonical[96:144];context[304:368]=canonical[96+shift:160+shift]
  overlap=max(0,min(base+48,base+shift+64)-max(base,base+shift))
  if bad and overlap:context[304+max(0,-shift)]^=1
  graph=SimpleNamespace(context=bytes(context),geometry=b'',offsets=b'',materials=b'',faces=b'');scene=SimpleNamespace(graph=graph)
  outcomes=[];objects=[]
  for cls in (Baseline,Candidate):
   try:m=cls(scene,b'');outcomes.append(m._ranges);objects.append(m)
   except ValueError:outcomes.append('conflict')
  assert outcomes[0]==outcomes[1]
  if outcomes[0]=='conflict':conflicts+=1
  else:
   for address in range(base-66,base+145,7):
    for size in (0,1,8,32,64,112):
     reads=[]
     for m in objects:
      try:reads.append(m.read(address,size))
      except ValueError:reads.append('unowned')
     assert reads[0]==reads[1]
  cases+=1
out=dict(result='PASS_OVERLAP_CONFLICT_AND_READ_BOUNDARY_PARITY',cases=cases,conflicts=conflicts,scope='Deterministic randomized bytes over290contained/adjacent/partial/disjoint snapshot pairs, cross-range/missing reads; does not establish broad ROM scene fidelity.')
Path('work/camera/prototype-runs/scene-merge-overlap-audit.json').write_text(json.dumps(out,indent=2));print(out)
