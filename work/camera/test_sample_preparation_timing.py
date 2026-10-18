from owned_precomputed_world_samples import PrecomputedWorldSamples
class Prepared:
 def __init__(self,fail=False):self.closed=0;self.fail=fail
 def sample(self,a):
  if self.fail:raise ValueError('sample failed')
  return (b'frame',None,None,None,{'alpha':a})
 def close(self):self.closed+=1
for trace in (False,True):
 p=Prepared();r=PrecomputedWorldSamples(p,(0,.5,1),trace=trace)
 assert p.closed==1 and r.sample(.5)[4]=={'alpha':.5}
 assert len(r.sample_timings)==(3 if trace else 0)
 for t in r.sample_timings:assert t['wall_ns']==t['completed_ns']-t['started_ns'] and t['thread_cpu_ns']>=0
 assert (r.prepared_close_ns is not None)==trace
 r.close();assert r.bytes==0 and not r.samples
 p=Prepared(True)
 try:PrecomputedWorldSamples(p,(.5,),trace=trace);raise AssertionError('error lost')
 except ValueError:assert p.closed==1
print('PASS: per-sample timing bounds, unchanged samples, cleanup on success/failure, tracing optional')
