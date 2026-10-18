import json,sys,time,random,statistics
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_scene_memory import ClosedSceneMemory
scope={};exec(compile(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/scene-memory-owned-ranges-20261006/before.py').read_text(),'before.py','exec'),scope);Old=scope['ClosedSceneMemory']
r=json.loads(Path(sys.argv[1]).read_text());rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();times=[[],[]];checks=0;rng=random.Random(620061)
for c in r['model_scene_captures']:
 g=ClosedGraph.decode(Path(c['graph']).read_bytes())
 for repeat in range(4):
  result=[None,None]
  for i in ((0,1) if repeat%2==0 else (1,0)):
   start=time.perf_counter_ns();result[i]=(Old if i==0 else ClosedSceneMemory)(g,rom);times[i].append(time.perf_counter_ns()-start)
  a,b=result;assert dict(a.owned)==dict(b.owned);assert a._owned_addresses==b._owned_addresses
  addresses=a._owned_addresses
  for _ in range(100):
   address=rng.choice(addresses)+rng.randrange(-5,5);size=rng.randrange(0,80);values=[]
   for m in (a,b):
    try:values.append(('ok',m.read(address,size)))
    except ValueError:values.append(('missing',m.missing[-1]))
   assert values[0]==values[1],(address,size);checks+=1
result=dict(exact_random_reads=checks,exact_maps=32,reference_build_median_ms=statistics.median(times[0])/1e6,candidate_build_median_ms=statistics.median(times[1])/1e6,reference_total_ms=sum(times[0])/1e6,candidate_total_ms=sum(times[1])/1e6,scope='cold owned memory construction and reads; not live timing')
Path('work/camera/prototype-runs/scene-memory-owned-ranges.json').write_text(json.dumps(result,indent=2));print(result)

from types import SimpleNamespace
import struct
context=bytearray(g.graph.context);struct.pack_into('<I',context,80,struct.unpack_from('<I',context,84)[0]);bad=SimpleNamespace(graph=SimpleNamespace(context=bytes(context),geometry=g.graph.geometry,offsets=g.graph.offsets,materials=g.graph.materials,faces=g.graph.faces))
for cls in (Old,ClosedSceneMemory):
 try:cls(bad,rom)
 except ValueError as error:assert 'Conflicting owned scene memory' in str(error)
 else:raise AssertionError('Conflicting overlap accepted')
print('PASS conflicting overlap rejection')
