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
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
import owned_wall_record_reuse_install_candidate
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

from owned_progressive_source_samples_candidate import ProgressiveSourceWorldSamples
history.close();full_frames=tuple(frames);reference=None
import time,statistics
import owned_portal_traversal as traversal
import owned_motion_visibility as visibility
import owned_sampled_graph_wall_visibility as wall_visibility
from owned_sampled_graph_record_reuse_candidate import RecordCache
originals=dict(wall_record=RecordCache.encode,wall_edge=wall_visibility.sampled_edge)
metrics={};profiles=[]
def wrapped(name):
 original=originals[name]
 def call(*args,**kwargs):
  begin=time.perf_counter_ns()
  try:return original(*args,**kwargs)
  finally:
   count,wall=metrics.get(name,(0,0));metrics[name]=(count+1,wall+time.perf_counter_ns()-begin)
 return call

timings={False:[],True:[]}
for iteration in range(8):
 for reduced in ((False,True) if iteration%2==0 else (True,False)):
  metrics.clear()
  RecordCache.encode=wrapped('wall_record') if reduced else originals['wall_record']
  wall_visibility.sampled_edge=wrapped('wall_edge') if reduced else originals['wall_edge']
  started=time.perf_counter_ns()
  frames=[]
  for key,frame in enumerate(full_frames):
   frames.append(frame)
  history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh']
  prepared=samples=None
  try:
   prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
   portal=prepared.pair.portal
   samples=ProgressiveSourceWorldSamples(prepared,(.125,.25,.375,.5,.625,.75,.875))
   cache=portal._complete_wall_record_cache
   assert cache.hits>0 and cache.misses>0 and cache.records=={} and cache.bytes==0
   values=[]
   for alpha in samples.samples:
    frame,camera,models,bounds,detail=samples.sample(alpha);packed=samples.source_masks[alpha]
    values.append((frame,bytes(camera),bytes(models),bytes(bounds),detail,bytes(packed[0]),bytes(packed[1]),packed[2:]))
   if reference is None:reference=values
   else:assert values==reference
  finally:
   if samples:samples.close()
   if prepared:prepared.close()
   history.close()
  if reduced:profiles.append(dict(round=iteration,cache_hits=cache.hits,cache_misses=cache.misses,cache_released=True,scopes={k:dict(calls=v[0],wall_ms=v[1]/1e6) for k,v in metrics.items()}))
  timings[reduced].append((time.perf_counter_ns()-started)/1e6)
RecordCache.encode=originals['wall_record'];wall_visibility.sampled_edge=originals['wall_edge']
assert len(profiles)==8 and all(set(row['scopes'])==set(originals) for row in profiles)
summary={k:dict(median_calls=statistics.median(row['scopes'][k]['calls'] for row in profiles),median_wall_ms=statistics.median(row['scopes'][k]['wall_ms'] for row in profiles)) for k in originals}
result=dict(result='PASS_CURRENT_WALL_RECORD_SCOPE_PARITY',rounds=8,fractions=7,summary=summary,rows=profiles,scope='Captured full preparation exact source parity with current live-worker complete wall-record reuse and wall-edge scopes. Wall totals include instrumentation and overlap; cached endpoint calls do not equal computation cost. No live cadence claim.')
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(result['result']);print(summary)
