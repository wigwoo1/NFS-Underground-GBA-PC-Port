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

import os,time,statistics
import owned_sampled_graph_wall_visibility as visibility
candidate_source=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010/wall-offset-equality-candidate.py').read_text()
exec(compile(candidate_source,'wall_offset_equality_component_candidate','exec'),visibility.__dict__)
from owned_sampled_graph_wall_visibility import selected_graph_walls
history.close();timings={};reference=None
for enabled in (False,True):
 os.environ['NFSUG_WALL_OFFSET_EQUALITY_REUSE']='1' if enabled else '0'
 history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh']
 prepared=None;elapsed=[]
 try:
  prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
  for repeat in range(8):
   began=time.perf_counter_ns();outputs=[selected_graph_walls(prepared.pair.portal,a) for a in (.125,.25,.375,.5,.625,.75,.875)];elapsed.append((time.perf_counter_ns()-began)/1e6)
   if reference is None:reference=outputs
   else:assert outputs==reference
  timings[str(enabled)]=statistics.median(elapsed)
 finally:
  if prepared:prepared.close()
  history.close()
from types import SimpleNamespace
from owned_wall_offset_equality_reuse import offsets_equal
old=object();new=object();other=object();portal=SimpleNamespace(older=old,newer=new);calls=[]
def metadata(p,g):
 calls.append(g);return None,None,({1:b'old'} if g is old else {1:b'new'})
assert not offsets_equal(portal,metadata);assert not offsets_equal(portal,metadata);assert len(calls)==2
portal.newer=other;assert not offsets_equal(portal,metadata);assert len(calls)==4
result=dict(result='PASS_OFFSET_EQUALITY_REUSE_COMPONENT',fractions=7,rounds=8,median_ms=timings,negative_cached_rejection=True,owner_change_revalidated=True,scope='Same captured pair wall-selection outputs; no complete source/GPU pixels/live performance proof, opt-in only.')
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(result)
