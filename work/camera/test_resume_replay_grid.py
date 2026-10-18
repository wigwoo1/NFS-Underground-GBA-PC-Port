from owned_resume_scene_chain import ResumeSceneChain
from owned_motion_clock import scene_samples
class Scene:
 def __init__(self,r):self.identity=(2,r)
 def match(self,f):assert f==str(self.identity[1]).encode()
c=ResumeSceneChain(9)
for r in (8784,8787,8791,8794,8798,8801,8805,8808,8811):c.append(str(r).encode(),Scene(r))
origin=123456789;pause=199314000
p=c.replay_plan((2,8801),(2,8805),60,origin+pause,8754,12)
slots=[s for _,_,ss in p for s in ss]
original=[s for a,b,_ in p for s in scene_samples(origin,8754,a[1].identity[1],b[1].identity[1],12) if s['index']>60]
assert slots and slots[0]['index']==61
assert [s['index'] for s in slots]==list(range(61,slots[-1]['index']+1))
for a,b in zip(slots,original):
 assert a['index']==b['index'] and a['alpha']==b['alpha'] and a['deadline_ns']==b['deadline_ns']+pause
for last in (-1,59,65):
 try:c.replay_plan((2,8801),(2,8805),last,origin,8754,12);raise AssertionError('Invalid committed slot accepted')
 except ValueError:pass
print('PASS: captured scene chain resumes at61, contiguous exact60Hz slots, unchanged source alpha, exact pause-only clock shift, invalid committed boundaries rejected')
