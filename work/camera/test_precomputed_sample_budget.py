from owned_precomputed_world_samples import PrecomputedWorldSamples
class Prepared:
 def __init__(self):self.closed=0
 def sample(self,alpha):return bytes(32),None,None,None,{}
 def close(self):self.closed+=1
for alphas,budget in (((.5,.5),100),((.5,),16),(tuple(i/10 for i in range(9)),1000)):
 prepared=Prepared()
 try:PrecomputedWorldSamples(prepared,alphas,budget)
 except ValueError:pass
 else:raise AssertionError('Invalid sample set accepted')
 assert prepared.closed==1
prepared=Prepared();owned=PrecomputedWorldSamples(prepared,(.5,));assert prepared.closed==1 and owned.bytes==32
owned.close();owned.close();assert not owned.samples and owned.bytes==0
print('PASS sample count/memory/identity bounds and exact prepared scratch cleanup')
