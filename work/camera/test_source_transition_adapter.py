import json,struct,hashlib,ctypes as C
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
root=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/live-source-context-20261007/failure-snapshot');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();frames=[];scenes=[]
for label in ('older','newer'):
 frames.append((root/(label+'.frame.bin')).read_bytes());g=ClosedGraph(struct.unpack_from('<Q',frames[-1],24)[0],struct.unpack_from('<I',frames[-1],4)[0],GraphPacket.decode((root/(label+'.graph.bin')).read_bytes()),*((root/(label+'.'+field+'.bin')).read_bytes() for field in ('objects','callbacks','associations')));scenes.append(MotionScene(g,ClosedSupplements.decode((root/(label+'.supplements.bin')).read_bytes(),g,rom),OwnedModelBuilders((root/(label+'.builders.bin')).read_bytes()),OwnedModelSources.decode((root/(label+'.current-sources.bin')).read_bytes(),g)))
table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);history=EndpointRoadPlanner(rom,table);roads,_=history.plan(scenes[0].graph);prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);samples=[]
try:
 for alpha in (0,.1,.25,.5,.75,.99,1):
  frame,camera,models,bounds,detail=prepared.sample(alpha);rows=records(frame)['records'];samples.append(dict(alpha=alpha,model_keys=[r['key'] for r in rows if r['kind']==3]))
  if alpha in (0,1):assert frame==frames[int(alpha)]
 from owned_source_presentation_batch_candidate import prepare_source_models
 from owned_source_face_mask_candidate import build_source_face_mask
 gpu=C.CDLL(str(Path('work/camera/owned-sky-source-context-candidate.dll').resolve()));native_table=(C.c_uint32*32768)(*table)
 anchors,classifiers=prepare_source_models(prepared,gpu,native_table);mask_checks=[]
 for alpha in (.1,.25,.5,.75,.99):
  frame,camera,models,bounds,detail=prepared.sample(alpha);anchored=anchors.sample(frame,models,alpha);offsets,mask,total,diagnostic=build_source_face_mask(frame,anchored,bounds,alpha,classifiers)
  assert total==51 and len(anchors.preanchored_keys)==1
  mask_checks.append(dict(alpha=alpha,total_faces=total,**diagnostic))
 pairs=[]
 for owner,pair in prepared.pair._scenery_record_pairs.items():
  assert all(pair.older_blocks[i]==pair.newer_blocks[i] for i in (1,4,5,6,7,8,10))
  pairs.append(dict(owner=owner,older_allocated=pair.older_allocated,newer_allocated=pair.newer_allocated,raw_matrices=[list(struct.unpack('<12i',b[2])) for b in (pair.older_blocks,pair.newer_blocks)]))
 result=dict(result='PASS_SOURCE_TRANSITION_ADAPTER',mask_checks=mask_checks,preanchored_scenery_keys=list(anchors.preanchored_keys),refreshes=[s.graph.refresh for s in scenes],samples=samples,source_pairs=pairs,deactivation=prepared.pair._scenery_deactivation,depth_exit=list(prepared.pair._scenery_depth_exit),portal_exit=list(prepared.pair._scenery_portal_exit),scope='Actual failed scene pair reconstructs source-owned scenery matrices and visibility transitions; no queued candidate integration or cadence claim.')
finally:prepared.close();history.close()
hashes=json.loads(Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-committed-sample-20261006/protected-hashes.json').read_text());assert all(hashlib.sha256(Path(k).read_bytes()).hexdigest().upper()==v for k,v in hashes.items());result['protected_assets']='PASS'
out=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/source-transition-adapter-20261007');out.mkdir(exist_ok=True);(out/'tests.json').write_text(json.dumps(result,indent=2));(out/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print(json.dumps(result,indent=2))
