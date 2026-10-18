"""Exact sparse construction, overlaps and reads against retained implementation."""
import json,struct,random,time,statistics
from pathlib import Path
from types import SimpleNamespace
import owned_closed_scene_memory as memory
scope={};exec(Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-scene-memory-batch-20261006/before.py').read_text(),scope);Old=scope['ClosedSceneMemory'];New=memory.ClosedSceneMemory
rng=random.Random(20261006);read_checks=0;conflicts=0;times={'before':[],'after':[]}
master=bytes(rng.randrange(256) for _ in range(8192));base=0x02001000
for trial in range(60):
 context=bytearray(368);struct.pack_into('<I',context,84,base);struct.pack_into('<I',context,80,base+100);context[256:304]=master[:48];context[304:368]=master[100:164]
 records=[]
 for index in range(200):
  offset=rng.randrange(len(master)-48);records.append(struct.pack('<4I',index,0,base+offset,0)+master[offset:offset+48])
 graph=SimpleNamespace(context=bytes(context),geometry=b''.join(records),offsets=b'',materials=b'',faces=b'');scene=SimpleNamespace(graph=graph)
 instances={}
 for label,cls in (('before',Old),('after',New)) if trial%2==0 else (('after',New),('before',Old)):
  start=time.perf_counter_ns();instances[label]=cls(scene,b'');times[label].append(time.perf_counter_ns()-start)
 a,b=instances.values();assert a._ranges==b._ranges and a.owned_byte_count==b.owned_byte_count
 for _ in range(30):
  address=base+rng.randrange(len(master));size=rng.randrange(100);results=[]
  for m in (a,b):
   try:results.append(('ok',m.read(address,size)))
   except ValueError as error:results.append(('error',str(error),m.missing[-1]))
  assert results[0]==results[1];read_checks+=1
 # Duplicate and nested overlap: any altered owned byte must still reject.
 for offset in (0,12,30):
  changed=bytearray(master[offset:offset+48]);changed[0]^=1
  bad=SimpleNamespace(graph=SimpleNamespace(context=bytes(context),geometry=graph.geometry+struct.pack('<4I',999,0,base+offset,0)+changed,offsets=b'',materials=b'',faces=b''))
  for cls in (Old,New):
   try:cls(bad,b'')
   except ValueError as error:assert str(error)=='Conflicting owned scene memory';conflicts+=1
   else:raise AssertionError('Conflicting overlap accepted')
result=dict(result='PASS',maps=60,random_reads=read_checks,conflict_rejections=conflicts,construction_median_ms={k:statistics.median(v)/1e6 for k,v in times.items()},scope='Random overlapping sparse ranges, exact immutable map and errors; component timings only')
out=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-scene-memory-batch-20261006');(out/'range-tests.json').write_text(json.dumps(result,indent=2));print(result)
