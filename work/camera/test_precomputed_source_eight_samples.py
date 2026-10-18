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
 result=dict(result='PASS_PRECOMPUTED_SOURCE_SAMPLES',mask_checks=mask_checks,preanchored_scenery_keys=list(anchors.preanchored_keys),refreshes=[s.graph.refresh for s in scenes],samples=samples,source_pairs=pairs,deactivation=prepared.pair._scenery_deactivation,depth_exit=list(prepared.pair._scenery_depth_exit),portal_exit=list(prepared.pair._scenery_portal_exit),scope='Actual failed scene pair reconstructs source-owned scenery matrices and visibility transitions; no queued candidate integration or cadence claim.')
 from owned_precomputed_source_samples_candidate import PrecomputedSourceWorldSamples
 alphas=(.001,.1,.25,.5,.75,.9,.99,.999);expected={}
 for alpha in alphas:
  frame,camera,models,bounds,detail=prepared.sample(alpha);anchored=anchors.sample(frame,models,alpha);packed=build_source_face_mask(frame,anchored,bounds,alpha,classifiers)
  expected[alpha]=(frame,bytes(camera),bytes(anchored),bytes(bounds),bytes(packed[0]),bytes(packed[1]),packed[2])
 cached=PrecomputedSourceWorldSamples(prepared,alphas,trace=True)
 import gc
 gc.collect()
 portal=prepared.pair.portal
 assert all(len(getattr(portal,name,()))<=2 for name in ('_wall_material_cache','_wall_source_cache','_wall_metadata_cache'))
 prepared.close()
 assert all(not getattr(portal,name,()) for name in ('_wall_material_cache','_wall_source_cache','_wall_metadata_cache'))
 result['closed_wall_caches_empty']=True
 for alpha in alphas:
  frame,camera,models,bounds,detail=cached.sample(alpha);packed=cached.source_masks[alpha]
  assert (frame,bytes(camera),bytes(models),bytes(bounds),bytes(packed[0]),bytes(packed[1]),packed[2])==expected[alpha]
 assert cached.bytes>0 and len(cached.source_cameras)==4
 assert len(cached.sample_timings)==len(alphas)
 for t in cached.sample_timings:
  assert [x['name'] for x in t['source_sample_stages']]==['world_sample','model_anchors','source_face_mask','sample_publication']
  assert sum(x['wall_ns'] for x in t['source_sample_stages'])==t['wall_ns']==t['completed_ns']-t['started_ns']
  assert all(x['wall_ns']>=0 and x['thread_cpu_ns']>=0 and x['thread_cycles']>=0 for x in t['source_sample_stages'])
 result['stage_accounting_exact']=True
 result['sample_byte_checks']=[dict(alpha=a,frame_sha256=hashlib.sha256(expected[a][0]).hexdigest(),model_sha256=hashlib.sha256(expected[a][2]).hexdigest(),mask_sha256=hashlib.sha256(expected[a][5]).hexdigest(),direct_equals_prepared=True) for a in alphas]
 result['comparison_scope']='Direct current implementation vs precomputed candidate; not independent original fractional oracle or GPU pixel comparison'
 result['prepared_source_samples']=len(alphas);result['private_prepared_bytes']=cached.bytes;result['exact_after_original_pair_close']=True
 cached.close();assert cached.bytes==0 and not cached.samples and not cached.source_masks and not cached.source_cameras
 result['bounded_cleanup']=True
finally:prepared.close();history.close()
hashes=json.loads(Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-committed-sample-20261006/protected-hashes.json').read_text());assert all(hashlib.sha256(Path(k).read_bytes()).hexdigest().upper()==v for k,v in hashes.items());result['protected_assets']='PASS'
out=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/precomputed-source-eight-samples-20261007');out.mkdir(exist_ok=True);(out/'tests.json').write_text(json.dumps(result,indent=2));(out/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print(json.dumps(result,indent=2))

