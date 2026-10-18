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

import owned_source_face_mask_candidate as mask
import owned_source_mask_stage_trace as trace
from owned_progressive_source_samples_candidate import ProgressiveSourceWorldSamples
history.close();reference=None
for enabled in (False,True):
 mask._stage_trace=trace if enabled else None
 history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh']
 prepared=None;samples=None
 try:
  prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
  samples=ProgressiveSourceWorldSamples(prepared,(.125,.25,.375,.5,.625,.75,.875))
  output=[]
  for alpha in samples.samples:
   frame,camera,models,bounds,detail=samples.sample(alpha);packed=samples.source_masks[alpha]
   output.append((frame,bytes(camera),bytes(models),bytes(bounds),detail,bytes(packed[0]),bytes(packed[1]),packed[2:]))
  if reference is None:reference=output
  else:assert reference==output
 finally:
  if samples:samples.close()
  if prepared:prepared.close()
  history.close()
result=dict(result='PASS_MASK_STAGE_TRACE_PARITY',samples=len(reference),trace=trace.snapshot(),scope='Actual captured pair source outputs/masks equal with trace off/on. Component only; no GPU or live cadence proof.')
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(result['result'],result['samples'])
