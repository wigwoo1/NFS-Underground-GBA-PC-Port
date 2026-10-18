from owned_resume_scene_chain import ResumeSceneChain
from owned_motion_clock import scene_samples
class Scene:
 def __init__(self,r):self.identity=(2,r)
 def match(self,f):assert f==str(self.identity[1]).encode()
c=ResumeSceneChain(9)
for r in (8754,8758,8762,8766,8769,8773,8776):c.append(str(r).encode(),Scene(r))
origin=123456789;shift=200000000
plan=c.initial_replay_plan(origin,8754,12);shifted=c.initial_replay_plan(origin+shift,8754,12)
expected=[s for a,b in zip(tuple(c.items.values()),tuple(c.items.values())[1:]) for s in scene_samples(origin,8754,a[1].identity[1],b[1].identity[1],12)]
actual=[s for _,_,slots in plan for s in slots];later=[s for _,_,slots in shifted for s in slots]
assert actual==expected and actual and [s['index'] for s in actual]==list(range(actual[0]['index'],actual[-1]['index']+1))
assert all(a['index']==b['index'] and a['alpha']==b['alpha'] and b['deadline_ns']-a['deadline_ns']==shift for a,b in zip(actual,later))
empty=ResumeSceneChain(3)
for count in (0,1):
 if count:empty.append(b'8754',Scene(8754))
 try:empty.initial_replay_plan(origin,8754,12)
 except ValueError:pass
 else:raise AssertionError('Unowned initial interval accepted')
print('PASS initial pending source grid, exact alpha/index, pause-only deadline shift, empty/single-source rejection')
