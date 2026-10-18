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

from owned_progressive_source_samples_candidate import ProgressiveSourceWorldSamples
history.close();full_frames=tuple(frames);reference=None
import time,statistics
import os
os.environ['NFSUG_WALL_CANDIDATE_TRACE']='1'
import owned_motion_wall_regions as regions
import owned_sampled_graph_wall_visibility as visibility
profile_rows=[]
timings={False:[],True:[]}
for iteration in range(8):
 for reduced in ((False,True) if iteration%2==0 else (True,False)):
  visibility.wall_region_candidates=regions._traced_wall_region_candidates if reduced else regions._plain_wall_region_candidates
  started=time.perf_counter_ns()
  frames=[]
  for key,frame in enumerate(full_frames):
   frames.append(frame)
  history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh']
  prepared=samples=None
  try:
   prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
   samples=ProgressiveSourceWorldSamples(prepared,(.125,.25,.375,.5,.625,.75,.875),trace=True)
   if reduced:
    for sample in samples.sample_timings:
     for stage in sample['assembly_stages']:
      for v in stage.get('visibility_stages',[]):
       if v['name']=='candidate_generation':
        profile_rows.extend(dict(round=iteration,alpha=sample['alpha'],name=x['name'],wall_ms=x['wall_ns']/1e6,cycles=x['thread_cycles']) for x in v.get('candidate_stages',[]))
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
  timings[reduced].append((time.perf_counter_ns()-started)/1e6)
visibility.wall_region_candidates=regions._plain_wall_region_candidates
groups={}
for row in profile_rows:groups.setdefault((row['alpha']==.125,row['name']),[]).append(row['wall_ms'])
summary=[dict(first_sample=key[0],name=key[1],median_ms=statistics.median(value),max_ms=max(value),samples=len(value)) for key,value in groups.items()]
summary.sort(key=lambda x:(not x['first_sample'],-x['median_ms']))
assert len(profile_rows)==8*7*5
result=dict(result='PASS_WALL_CANDIDATE_SUBSTAGE_PARITY',rounds=8,fractions=7,summary=summary,rows=profile_rows,scope='Captured independent traced/untraced full preparation and source parity; substage wall timing with instrumentation, no live cadence claim.')
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(result['result']);print(summary)
