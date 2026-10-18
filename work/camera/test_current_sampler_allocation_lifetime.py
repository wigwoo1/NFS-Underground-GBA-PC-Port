import sys,json,gc,weakref,ctypes as C,types,collections,tracemalloc,hashlib
from pathlib import Path
folder=Path('work/camera/prototype-runs/child-scene-1791637661169682300')
setup=Path('work/camera/test_current_wall_record_scopes.py').read_text().split('from owned_progressive_source_samples_candidate import ProgressiveSourceWorldSamples')[0]
import owned_road_planner_library_install_candidate,owned_road_material_decode_install_candidate,owned_preparation_fixed_types_install_candidate
import owned_road_encode_flat_join_install_candidate,owned_road_record_worker_install_candidate
import owned_endpoint_road_planner as planner
from owned_endpoint_road_fixed_types_candidate import endpoint_road_span_candidates
planner.endpoint_road_span_candidates=endpoint_road_span_candidates
import owned_source_presentation_batch_candidate as batch
from owned_source_depth_transition_candidate import SourceFaceDeterminants
batch.SourceFaceDeterminants=SourceFaceDeterminants
import owned_frame_prefix_cache_candidate
owned_frame_prefix_cache_candidate.install()
sys.argv=['allocation',str(folder)];exec(compile(setup,'actual-captured-scene-setup','exec'))
from owned_progressive_source_samples_candidate import ProgressiveSourceWorldSamples,projection_table_owner,source_library_owner
import owned_rom_slice_reuse_install_candidate,owned_record_miss_container_reuse_install_candidate
projection_table_owner();source_library_owner();history.close()
alphas=(.01,.2,.4,.6,.8,.99);baseline_ids={id(x) for x in gc.get_objects()};tracemalloc.start(3);before=tracemalloc.take_snapshot();packets=[]
def publish(packet):
 packets.append(hashlib.sha256(bytes(packet[1])+b''.join(packet[2:7])+str(packet[7]).encode()+packet[8]+packet[9]+repr(packet[10]).encode()).hexdigest())
history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh']
prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);prepared_ref=weakref.ref(prepared)
samples=ProgressiveSourceWorldSamples(prepared,alphas,on_sample=publish);samples_ref=weakref.ref(samples);assert len(packets)==6
snapshot=tracemalloc.take_snapshot();objects=gc.get_objects();counts=collections.Counter();watched=[]
for obj in objects:
 if id(obj) in baseline_ids:continue
 typ=type(obj);label=typ.__module__+'.'+typ.__qualname__;counts[label]+=1
 if isinstance(obj,(types.FunctionType,C.Array,C._CFuncPtr,type)) and len(watched)<4096:
  try:
   if isinstance(obj,type):label+=':'+obj.__module__+'.'+obj.__qualname__
   watched.append((label,weakref.ref(obj)))
  except TypeError:pass
del obj,objects
samples.close();prepared.close();history.close();del samples,prepared,history
assert prepared_ref() is None and samples_ref() is None
alive=collections.Counter(name for name,ref in watched if ref() is not None)
# Explicit collection is confined to this offline diagnostic, never the live worker.
collected=gc.collect();after=collections.Counter(name for name,ref in watched if ref() is not None)
sites=[dict(bytes=x.size_diff,count=x.count_diff,traceback=[str(t) for t in x.traceback]) for x in snapshot.compare_to(before,'traceback')[:20]];tracemalloc.stop()
result=dict(result='PASS_CURRENT_SAMPLER_ALLOCATION_LIFETIME',sampler=ProgressiveSourceWorldSamples.__module__,packet_fingerprints=packets,packets=len(packets),prepared_and_sampler_released_without_collection=True,new_tracked_types=counts.most_common(20),watched=len(watched),alive_after_close=alive.most_common(20),alive_after_offline_collection=after.most_common(20),collected=collected,allocation_sites=sites,scope='One real captured pair/current sampler and complete wall record reuse; source packets consumed as hashes, postclose weakrefs bounded4096. Offline tracing/collection perturb timing, imports/caches and shallow tracking do not prove GC stall cause or long memory stability. No live policy change.')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010/current-sampler-allocation-lifetime.json').write_text(json.dumps(result,indent=2));print({k:result[k] for k in ['result','sampler','packets','prepared_and_sampler_released_without_collection','watched','alive_after_close','alive_after_offline_collection','collected']})
