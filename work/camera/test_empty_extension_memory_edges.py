import json,struct,random
from types import SimpleNamespace
from pathlib import Path
from owned_closed_scene_memory import ClosedSceneMemory as Baseline
from owned_closed_scene_bulk_candidate import ClosedSceneMemory as Candidate
rom=bytes(range(256))*1024
base=0x02001000
payload=bytes(range(48))
def scene(ranges):
 context=bytearray(368);struct.pack_into('<I',context,84,0x03000000);struct.pack_into('<I',context,80,0x03000100)
 geometry=b''.join(struct.pack('<4I',i,0,address,0)+data for i,(address,data) in enumerate(ranges))
 return SimpleNamespace(graph=SimpleNamespace(context=bytes(context),geometry=geometry,offsets=b'',materials=b'',faces=b''))
fixtures=[('same',[(base,payload),(base,payload)]),('contained',[(0x03000108,b'\0'*48)]),('partial',[(base,payload),(base+24,payload[24:]+bytes(range(48,72)))]),('adjacent',[(base,payload),(base+48,payload)]),('disjoint',[(base,payload),(base+80,payload)]),('ROM',[(0x08000010,payload)]),('conflict_contained',[(0x03000108,b'X'*48)]),('conflict_same',[(base,payload),(base,b'X'*48)]),('conflict_partial',[(base,payload),(base+24,b'X'*48)])]
checks=0;conflicts=0
for name,ranges in fixtures:
 results=[]
 for cls in (Baseline,Candidate):
  try:results.append(cls(scene(ranges),rom))
  except ValueError as error:results.append(str(error))
 a,b=results
 if isinstance(a,str):assert a==b=='Conflicting owned scene memory';conflicts+=1;continue
 assert (a._ranges,a._starts,a.owned_byte_count)==(b._ranges,b._starts,b.owned_byte_count)
 requests=[(base,72),(base+47,2),(base+49,1),(0x08000000,80),(0x08000020,20),(0x01000000,1),(base,0),(base,-1),(0xffffffff,2),(base,0x100001)]
 requests+=[(start,max(1,len(data)//2)) for start,data in a._ranges]
 for address,size in requests:
  values=[]
  for owner in (a,b):
   try:values.append(('bytes',owner.read(address,size)))
   except ValueError as error:values.append(('error',str(error)))
  assert values[0]==values[1],(name,address,size);checks+=1
 assert a.missing==b.missing
out=dict(result='PASS_EMPTY_EXTENSION_OWNERSHIP_EDGE_PARITY',fixtures=len(fixtures),conflict_cases=conflicts,read_checks=checks,scope='Synthetic fixed48byte descriptor ranges plus previous real-scene parity; no live/full4K cadence proof.')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010/empty-extension-edge-parity.json').write_text(json.dumps(out,indent=2));print(out)
