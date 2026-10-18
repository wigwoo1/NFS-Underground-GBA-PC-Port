from owned_resume_scene_chain import ResumeSceneChain
class Scene:
 def __init__(self,r,epoch=2):self.identity=(epoch,r)
 def match(self,f):assert f==bytes([self.identity[1]])
c=ResumeSceneChain(4)
a=bytearray([1]);c.append(a,Scene(1));a[0]=99
for r in (2,3,4):c.append(bytes([r]),Scene(r))
assert [x[1].identity[1] for x in c.suffix((2,1),(2,2))]==[1,2,3,4]
assert c.suffix((2,1),(2,2))[0][0]==b'\x01'
c.append(b'\x05',Scene(5));assert len(c.items)==4
for fn in (lambda:c.suffix((2,1),(2,2)),lambda:c.suffix((2,2),(2,4)),lambda:c.append(b'\x05',Scene(5)),lambda:c.append(b'\x06',Scene(6,3))):
 try:fn();raise AssertionError('Invalid chain accepted')
 except ValueError:pass
c.clear();assert not c.items and c.epoch is None
print('PASS: immutable copy, displayed-boundary suffix, bounded eviction, missing/nonadjacent/duplicate/epoch rejection and cleanup')
