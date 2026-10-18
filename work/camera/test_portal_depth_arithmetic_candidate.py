from pathlib import Path
import sys,struct,random,json
sys.path.insert(0,str(Path('work/camera').resolve()))
import owned_portal_continuous as baseline
from owned_portal_depth_projection_candidate import edge as candidate
r=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);rng=random.Random(73104);count=0;rejected=0
for i in range(20000):
 x=rng.choice([-100000.,-1.,0.,1.,2.,100000.])+rng.choice([0.,.0000001,.25,.5,.9999999]);nx=rng.uniform(-100000,100000)
 z=rng.choice([0.,1.,16.,256.,4096.,32766.,32767.])+rng.choice([0.,.25,.9999999]);nz=rng.uniform(0,32768)
 args=((x,z),(nx,nz),rng.choice([1,16,256]),rng.choice([0,1,256,65535,2147483647,4294967295]),rng.choice([-32768,0,120,32767]),r,bool(i%2))
 def outcome(fn):
  try:return ('value',fn(*args))
  except ValueError as e:return ('error',str(e))
 a,b=outcome(baseline.edge),outcome(candidate);assert a==b,(i,args[:5],a,b)
 count+=1;rejected+=a[0]=='error'
out=dict(result='PASS_EXACT_PORTAL_DEPTH_ARITHMETIC',cases=count,rejected_identically=rejected,scope='Deterministic finite-domain boundary/random edge projection, signed wrapping, integer/fractional cells and near clipping. No fullscene GPU or live60 proof.')
Path('outputs/nfsug-native-renderer/camera-research/portal-depth-arithmetic-20261009.json').write_text(json.dumps(out,indent=2));print(out)
