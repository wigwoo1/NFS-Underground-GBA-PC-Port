"""Candidate motion changes continuously, is reversible, and preserves endpoints."""
import runpy,math
from dataclasses import replace
from owned_scenery_motion import PreparedSceneryMotion,normalized_matrix
v=runpy.run_path('work/camera/test_activation_scenery_record_pairs.py');pairs=v['pairs'];cameras=[s.graph.graph.context[256:304] for s in v['scenes']]
motion=PreparedSceneryMotion(pairs,*cameras);reverse=PreparedSceneryMotion([replace(p,older_blocks=p.newer_blocks,newer_blocks=p.older_blocks) for p in pairs],*reversed(cameras));checks=0;largest_step=0;endpoint_limits=[]
for pair in pairs:
 samples=[motion.matrix(pair.object_index,i/100) for i in range(101)]
 assert samples[0]==normalized_matrix(pair.older_blocks[2]) and samples[-1]==normalized_matrix(pair.newer_blocks[2])
 assert len(set(samples))==101,'Scenery poses held during motion'
 for i in range(1,100):
  backward=reverse.matrix(pair.object_index,1-i/100)
  assert max(abs(a-b) for a,b in zip(samples[i],backward))<1e-8
  checks+=1
 for a,b in zip(samples,samples[1:]):largest_step=max(largest_step,max(abs(x-y) for x,y in zip(a,b)))
 limits=[max(abs(x-y) for x,y in zip(motion.matrix(pair.object_index,t),samples[endpoint])) for t,endpoint in ((1e-8,0),(1-1e-8,-1))];endpoint_limits.append(dict(object=pair.object_index,near_endpoint_error=limits))
 assert max(limits)<1e-5,'Rigid source decoding introduces large endpoint discontinuity'
for invalid in (-.1,1.1,float('nan'),float('inf')):
 try:motion.matrix(pairs[0].object_index,invalid)
 except ValueError:pass
 else:raise AssertionError('Invalid sample alpha accepted')
try:motion.matrix(999,.5)
except ValueError:pass
else:raise AssertionError('Unknown motion source accepted')
print(dict(result='PASS_SOURCE_SCENERY_MOTION',matrices=505,reversible_interior_checks=checks,largest_component_step=largest_step,endpoint_limits=endpoint_limits,scope='Candidate matrix component only; visibility timing and live scene integration pending.'))
