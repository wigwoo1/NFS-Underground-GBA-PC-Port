import os,time,statistics,json,gc,hashlib
from pathlib import Path
os.environ['NFSUG_PROJECTION_TYPE_COMPONENT']='0'
setup=Path('work/camera/test_projection_array_type_component.py').read_text().split('alphas=(.01,.2,.4,.6,.8,.99)')[0];exec(compile(setup,'matched-current-helpers','exec'))
import owned_geometry_range_reuse_candidate as reuse
import owned_closed_scene_memory as memory
original=memory.ClosedSceneMemory;reuse.clear();alphas=(.01,.2,.4,.6,.8,.99);timings={False:[],True:[]};reference=None
try:
 for iteration in range(16):
  for selected in ((False,True) if iteration%2==0 else (True,False)):
   memory.ClosedSceneMemory=reuse.ClosedSceneMemory if selected else original
   memory._scene_memory_local.entries=[]
   history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh'];packets=[]
   def publish(packet):packets.append(hashlib.sha256(bytes(packet[1])+b''.join(packet[2:7])+str(packet[7]).encode()+packet[8]+packet[9]+repr(packet[10]).encode()).hexdigest())
   began=time.perf_counter_ns();prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);samples=ProgressiveSourceWorldSamples(prepared,alphas,on_sample=publish);timings[selected].append((time.perf_counter_ns()-began)/1e6)
   assert len(packets)==6
   if reference is None:reference=packets
   assert packets==reference
   samples.close();prepared.close();history.close()
finally:memory.ClosedSceneMemory=original;memory._scene_memory_local.entries=[]
assert reuse.stats['hits']>0 and reuse.stats['misses']>0 and reuse.stats['bypasses']==0
out=dict(selection_stats=dict(reuse.stats),result='PASS_REPEATED_GEOMETRY_RANGE_SOURCE_PARITY',rounds=16,preparations=32,packets_exact=192,baseline_median_ms=statistics.median(timings[False]),candidate_median_ms=statistics.median(timings[True]),timings=timings,scope='Alternating complete capturedpair current sampler preparation+packet fingerprint cost, same process/caches; onevertex topology, diagnosticcomponent not live or diverse scene performance. No automatic GC policy change.')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/geometry-range-reuse-20261010/repeated.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='timings'})
