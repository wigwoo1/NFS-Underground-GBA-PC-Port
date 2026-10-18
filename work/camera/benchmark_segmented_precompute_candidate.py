import json,time,statistics
from pathlib import Path
source=Path('work/camera/test_prepared_world_release_candidate.py').read_text().split('results=[]')[0];exec(compile(source,'captured_setup','exec'))
from owned_prepared_world_segmented_candidate import PreparedWorldMotion as Segmented
from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
from owned_segmented_frame_candidate import SegmentedFrame
rows=[]
for iteration in range(8):
 order=[('contiguous',Candidate),('segmented',Segmented)]
 if iteration%2:order.reverse()
 signatures=[]
 for name,cls in order:
  history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh']
  prepared=cls(*frames,*scenes,history,roads,rom)
  begin=time.perf_counter_ns();cached=PrecomputedSourceWorldSamples(prepared,alphas,trace=True);elapsed=time.perf_counter_ns()-begin
  samples=[cached.sample(a) for a in alphas];signatures.append([signature(x)['buffers'] for x in samples])
  framebytes=sum(len(x[0]) for x in samples);prefixbytes=sum(len(x[0].prefix) if isinstance(x[0],SegmentedFrame) else len(x[0]) for x in samples)
  joins=[stage['wall_ns'] for sample in cached.sample_timings for stage in sample['assembly_stages'] if stage['name']=='immutable_frame_join']
  rows.append(dict(iteration=iteration,mode=name,precompute_ns=elapsed,join_ns=joins,logical_frame_bytes=framebytes,new_frame_owner_bytes=prefixbytes,retained_bases=len({id(x[0].base) for x in samples}) if name=='segmented' else 0))
  cached.close();history.close();del samples,cached,prepared,history
 assert signatures[0]==signatures[1]
out=dict(result='PASS_ALTERNATING_SEGMENTED_PRECOMPUTE',pairs=8,rows=rows,median_precompute_ns={name:statistics.median(row['precompute_ns'] for row in rows if row['mode']==name) for name in ('contiguous','segmented')},scope='Alternating captured five-sample full precomputation; output signatures exact. Timing includes sample-close/cache-release; materialization only outside timing for oracle. No live60 proof.')
Path('work/camera/prototype-runs/segmented-precompute-benchmark-20261008.json').write_text(json.dumps(out,indent=2));print(out['median_precompute_ns']);print(rows[-2:])
