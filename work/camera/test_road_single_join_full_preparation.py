import json,time,statistics
from pathlib import Path
source=Path('work/camera/test_prepared_world_release_candidate.py').read_text().split('results=[]')[0];exec(compile(source,'captured_setup','exec'))
from owned_prepared_world_segmented_candidate import PreparedWorldMotion as Segmented
from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
from owned_segmented_frame_candidate import SegmentedFrame
import owned_complete_road_gpu as gpu_roads, owned_sampled_road_sequence as sampled_roads, owned_endpoint_road_planner as endpoint_roads
from owned_road_single_join_candidate import encode_road
modules=(gpu_roads,sampled_roads,endpoint_roads)
originals=tuple(m.encode_road for m in modules)
rows=[]
for iteration in range(8):
 order=[('baseline',Segmented),('candidate',Segmented)]
 if iteration%2:order.reverse()
 signatures=[]
 for name,cls in order:
  for module,original in zip(modules,originals):module.encode_road=encode_road if name=='candidate' else original
  begin=time.perf_counter_ns()
  history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh']
  prepared=cls(*frames,*scenes,history,roads,rom)
  cached=PrecomputedSourceWorldSamples(prepared,alphas,trace=True);elapsed=time.perf_counter_ns()-begin
  samples=[cached.sample(a) for a in alphas];signatures.append(([signature(x) for x in samples], [(bytes(cached.source_masks[a][0]),bytes(cached.source_masks[a][1]),cached.source_masks[a][2:]) for a in alphas]))
  framebytes=sum(len(x[0]) for x in samples);prefixbytes=sum(len(x[0].prefix) if isinstance(x[0],SegmentedFrame) else len(x[0]) for x in samples)
  joins=[stage['wall_ns'] for sample in cached.sample_timings for stage in sample['assembly_stages'] if stage['name']=='immutable_frame_join']
  rows.append(dict(iteration=iteration,mode=name,precompute_ns=elapsed,join_ns=joins,logical_frame_bytes=framebytes,new_frame_owner_bytes=prefixbytes,retained_bases=len({id(x[0].base) for x in samples}) if True else 0))
  cached.close();history.close();del samples,cached,prepared,history
 assert signatures[0]==signatures[1]
out=dict(result='PASS_ROAD_SINGLE_JOIN_FULL_PREPARATION',pairs=8,rows=rows,median_precompute_ns={name:statistics.median(row['precompute_ns'] for row in rows if row['mode']==name) for name in ('baseline','candidate')},scope='Alternating captured complete construction and precomputation; all sample buffers, details, source-mask bytes and selection metadata exact. Timing includes sample-close/cache-release; materialization only outside timing for oracle. No live60 proof.')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/road-single-join-20261010/full-preparation.json').write_text(json.dumps(out,indent=2));print(out['median_precompute_ns']);print(rows[-2:])
