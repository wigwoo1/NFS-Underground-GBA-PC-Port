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

from owned_precomputed_source_samples_candidate import PrecomputedSourceWorldSamples
from owned_source_presentation_batch_candidate import OwnedSourcePresentationBatch
from owned_preparation_pipeline import PreparationPipeline
from types import SimpleNamespace
from concurrent.futures import CancelledError
import threading,gc
table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072])
def make_cache():
 history=EndpointRoadPlanner(rom,table)
 try:
  roads,_=history.plan(scenes[0].graph);prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
  return PrecomputedSourceWorldSamples(prepared,(.25,.5,.75))
 finally:history.close()
pipeline=PreparationPipeline(2);checks=[]
try:
 future=pipeline.submit(make_cache);cache=future.result(10);assert cache.bytes>0;pipeline.invalidate()
 assert not cache.samples and not cache.source_masks and cache.bytes==0
 try:pipeline.take(future)
 except CancelledError:pass
 else:raise AssertionError('Retired ready result accepted')
 checks.append('ready_result_retired')
 entered=threading.Event();release=threading.Event();made=[]
 def delayed():
  cache=make_cache();made.append(cache);entered.set();assert release.wait(5);return cache
 future=pipeline.submit(delayed);assert entered.wait(10);pipeline.invalidate();release.set()
 try:future.result(10)
 except CancelledError:pass
 else:raise AssertionError('Retired running result published')
 assert made[0].bytes==0 and not made[0].source_masks;checks.append('running_result_retired')
 cache=pipeline.take(pipeline.submit(make_cache));gpu=C.CDLL(str(Path('work/camera/owned-sky-source-context-candidate.dll').resolve()))
 rows=[]
 for index,alpha in enumerate((.25,.5,.75)):
  sky=SimpleNamespace(lower=bytes([8])*15136,upper=bytes([9])*15136,weight=.3,destination=0x06002940)
  rows.append((9111,9115,index,100+index,alpha,cache.sample(alpha),sky))
 batch=OwnedSourcePresentationBatch(scenes[0].graph.epoch,rows,cache,gpu);snapshots=[]
 for draw in batch.source_draws:
  c=draw.context;count=c.draw.count
  snapshots.append((C.string_at(c.draw.frame,c.draw.bytes),C.string_at(c.draw.models,count*12*8),C.string_at(c.mask,c.total)))
 for value in cache.samples.values():
  for array in value[1:4]:
   for i in range(len(array)):array[i]=0
 for packed in cache.source_masks.values():
  for i in range(len(packed[1])):packed[1][i]=0
 cache.close();del cache;del rows;gc.collect()
 for draw,expected in zip(batch.source_draws,snapshots):
  c=draw.context;assert (C.string_at(c.draw.frame,c.draw.bytes),C.string_at(c.draw.models,c.draw.count*12*8),C.string_at(c.mask,c.total))==expected
 checks.append('taken_source_arrays_mutation_and_cache_retirement_preserve_batch')
finally:pipeline.close()
assert not pipeline.thread.is_alive() and not pipeline.ready
hashes=json.loads(Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-committed-sample-20261006/protected-hashes.json').read_text());assert all(hashlib.sha256(Path(k).read_bytes()).hexdigest().upper()==v for k,v in hashes.items())
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/source-preparation-retirement-20261007');cp.mkdir(exist_ok=True)
result=dict(result='PASS_SOURCE_PREPARATION_RETIREMENT',checks=checks,batch_contexts=3,pipeline_thread_stopped=True,protected_assets='PASS',scope='Actual captured transition through preparation pipeline cancellation/retirement and owned source batch storage; native GPU queue in-flight cancellation not exercised.')
(cp/'tests.json').write_text(json.dumps(result,indent=2));(cp/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print(json.dumps(result,indent=2))
