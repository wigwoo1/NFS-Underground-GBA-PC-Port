import random,struct,json
import owned_sampled_road_camera as original
import owned_road_camera_batch_candidate as candidate
r=random.Random(83017)
identity=(16384,0,0,0,16384,0,0,0,16384,0,0,0)
pose=(1.,0.,0.,0.,1.,0.,0.,0.,1.,0.,0.,0.)
def outcome(fn,args):
 try:return ('value',tuple(struct.pack('d',v) for v in fn(*args)))
 except Exception as e:return ('error',type(e).__name__,str(e))
cases=[]
for count in (0,1,2,8,32,33):
 for j in range(100):
  world=tuple(float(r.randint(-50000,50000)) for _ in range(count*3))
  camera=tuple(v+r.uniform(-.001,.001) for v in pose)
  cases.append((world,identity,identity,(pose,pose),camera,r.choice((0.,.1,.5,.9,1.))))
for world in ((1.,2.),(.5,0.,1.),(float('nan'),0.,1.),(float('inf'),0.,1.)):
 for alpha in (0.,.5,1.,-1.,float('nan')):cases.append((world,identity,identity,(pose,pose),pose,alpha))
for camera in (pose[:11],(float('nan'),)+pose[1:],(float('inf'),)+pose[1:]):
 cases.append(((1.,0.,2.),identity,identity,(pose,pose),camera,.5))
for name in ('sampled_road_camera','sampled_road_far_depths'):
 for args in cases:
  a=outcome(getattr(original,name),args);b=outcome(getattr(candidate,name),args)
  assert a==b,(name,args,a,b)
print(json.dumps(dict(result='PASS',comparisons=len(cases)*2,scope='Exact double output or exception type/text; endpoints, empty and oversized roads, fractional/nonfinite inputs, matrix length, signed wrap')))
