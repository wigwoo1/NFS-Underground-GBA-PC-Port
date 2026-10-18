import random,struct,time,statistics
from pathlib import Path
from owned_sampled_road_camera import _rigid,_rigid_depth,sampled_road_far_depths
before={};exec(Path('outputs/nfsug-native-renderer/camera-research/lifecycle/road-far-depth-axis-20261006/before.py').read_text(),before)
r=random.Random(624);cases=[(tuple(r.uniform(-1e5,1e5) for _ in range(3)),tuple(r.uniform(-1e3,1e3) for _ in range(12))) for _ in range(10000)]
for point,pose in cases:assert struct.pack('d',_rigid(point,pose)[2])==struct.pack('d',_rigid_depth(point,pose))
world=tuple(v for i in range(128) for v in (i*2,0,i*3+100));matrix=(16384,0,0,0,16384,0,0,0,16384,0,0,0);poses=(tuple(x/16384 if i<9 else x for i,x in enumerate(matrix)),)*2;camera=poses[0]
a=before['sampled_road_far_depths'];b=sampled_road_far_depths
for i in range(101):assert a(world,matrix,matrix,poses,camera,i/100)==b(world,matrix,matrix,poses,camera,i/100)
times=[[],[]]
for j in range(20):
 for index in ((0,1) if j%2==0 else (1,0)):
  begin=time.perf_counter_ns()
  for i in range(30):(a,b)[index](world,matrix,matrix,poses,camera,.37)
  times[index].append((time.perf_counter_ns()-begin)/1e6)
print('PASS10000 binary-exact depth transforms and101 complete depth arrays; median30calls ms',*[statistics.median(v) for v in times])
