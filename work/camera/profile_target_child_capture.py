"""Reconstruct captured closed scenes and verify endpoint identity and history."""
import sys,json,hashlib
from pathlib import Path
folder=Path(sys.argv[1]);manifest=json.loads((folder/'manifest.json').read_text())
for name,item in manifest['files'].items():
 data=(folder/name).read_bytes()
 assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256']
import json,struct,ctypes as C
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_graph_packet import GraphPacket
from owned_closed_supplements import ClosedSupplements
from owned_model_builder_inputs import OwnedModelBuilders
from owned_model_sources import OwnedModelSources
from owned_motion_scene import MotionScene
from owned_prepared_world_motion import PreparedWorldMotion
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_motion_pairs import records

rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);frames=[];scenes=[]
for name in ('older','newer'):
 raw_supp=(folder/(name+'.supplements.bin')).read_bytes();refresh=struct.unpack_from('<I',raw_supp,8)[0];epoch=struct.unpack_from('<Q',raw_supp,24)[0]
 graph=ClosedGraph(epoch,refresh,GraphPacket.decode((folder/(name+'.graph.bin')).read_bytes()),*((folder/(name+'.'+section+'.bin')).read_bytes() for section in ('objects','callbacks','associations')))
 scenes.append(MotionScene(graph,ClosedSupplements.decode((folder/(name+'.supplements.bin')).read_bytes(),graph,rom),OwnedModelBuilders((folder/(name+'.builders.bin')).read_bytes()),OwnedModelSources.decode((folder/(name+'.current-sources.bin')).read_bytes(),graph)))
 frames.append((folder/(name+'.frame.bin')).read_bytes())
from owned_road_history_diagnostic import restore
from owned_road_record_diagnostic import decode
h=json.loads((folder/'road-history.json').read_text());roads=decode(json.loads((folder/'older-roads.json').read_text()))
history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh']

import time,statistics,cProfile,pstats
import owned_closed_scene_memory as memory
history.close()
rows=[];reference=None
for repeat in range(5):
 memory._scene_memory_local.entries=[]
 history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh']
 prepared=None
 profiler=cProfile.Profile() if repeat==4 else None
 try:
  if profiler:profiler.enable()
  begin=time.perf_counter_ns();cpu=time.thread_time_ns()
  prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
  elapsed=time.perf_counter_ns()-begin;cpu_elapsed=time.thread_time_ns()-cpu
  if profiler:profiler.disable()
  samples=[]
  for alpha in (0,.125,.25,.375,.5,.625,.75,.875,1):
   result=prepared.sample(alpha)
   if alpha==0:assert result[0]==frames[0]
   if alpha==1:assert result[0]==frames[1]
   samples.append(hashlib.sha256(result[0]).hexdigest())
  if reference is None:reference=samples
  else:assert reference==samples
  rows.append(dict(repeat=repeat,profiled=bool(profiler),wall_ms=elapsed/1e6,cpu_ms=cpu_elapsed/1e6,stages=prepared.construct_stages))
 finally:
  if prepared:prepared.close()
  history.close()
 if profiler:
  stats=pstats.Stats(profiler)
  top=sorted(stats.stats.items(),key=lambda x:x[1][3],reverse=True)[:20]
  profile=[dict(file=k[0],line=k[1],function=k[2],calls=v[1],own_s=v[2],inclusive_s=v[3]) for k,v in top]
result=dict(result='PASS_TARGET_CAPTURE_REPLAY',older=manifest['older'],newer=manifest['newer'],rounds=rows,profile=profile,median_unprofiled_ms=statistics.median(x['wall_ms'] for x in rows if not x['profiled']),scope='Five isolated constructions with saved pre-advance road history and cold scene memory; repeated frame hashes and exact endpoints. No live cadence or GPU pixel qualification; assets/cache state differs from running child.')
Path(sys.argv[2]).write_text(json.dumps(result,indent=2))
print(result['result'],'median_ms',result['median_unprofiled_ms'])
for row in rows:print(row['repeat'],round(row['wall_ms'],3),[(s['name'],round(s['wall_ns']/1e6,3)) for s in row['stages']])
