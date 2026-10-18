import json,time,statistics
from pathlib import Path
source=Path('work/camera/test_prepared_world_release_candidate.py').read_text().split('results=[]')[0]
exec(compile(source,'capture_setup','exec'))
import owned_sampled_world_frame as assembly
from owned_native_frame_join_types_candidate import join_frame,helper,trace
reference=assembly.join_frame;helper()
history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh'];prepared=Candidate(*frames,*scenes,history,roads,rom)
native_trace=[]
timings={k:dict(join_ns=[],world_ns=[]) for k in ('reference','native')}
try:
 for iteration in range(40):
  order=[('reference',reference),('native',join_frame)]
  if iteration%2:order.reverse()
  values=[]
  for name,fn in order:
   assembly.join_frame=fn;begin=time.perf_counter_ns();sample=prepared.sample(.5);elapsed=time.perf_counter_ns()-begin
   stage=next(x for x in prepared.pair._last_sample_stages if x['name']=='immutable_frame_join')
   timings[name]['join_ns'].append(stage['wall_ns']);timings[name]['world_ns'].append(elapsed)
   if name=='native':native_trace.append(dict(trace()))
   values.append(signature(sample)['buffers'])
  assert values[0]==values[1]
finally:assembly.join_frame=reference;prepared.close();history.close()
out=dict(native_trace=native_trace,native_trace_medians_ns={k:statistics.median(x[k] for x in native_trace) for k in ('packing_ns','allocation_ns','native_call_ns')},result='PASS_ALTERNATING_NATIVE_JOIN_CAPTURED_PARITY',pairs=40,timings_ns=timings,medians_ns={name:{k:statistics.median(v) for k,v in row.items()} for name,row in timings.items()},scope='Alternating same captured scene alpha.5; exact four output buffers. Named join stage measured rather than final bounds stage. Host contention uncontrolled; no live60 claim.')
Path('work/camera/prototype-runs/native-join-types-benchmark-20261008.json').write_text(json.dumps(out,indent=2));print(out['medians_ns']);print(out['native_trace_medians_ns'])

