import ctypes as C,random,math,json
from pathlib import Path
from owned_source_batch_classify_candidate import _classify
from owned_source_native_depth_rectangle_candidate import determinant,source_rectangle_classify
rng=random.Random(57291);checks=0
for n in range(3,33):
 for trial in range(30):
  rect=(0.,0.,240.,160.);values=(-.500000001,-.5,-.499999999,239.499999999,239.5,239.500000001)
  points=tuple((rng.choice(values) if trial<15 else rng.uniform(-400,400),rng.choice(values) if trial<15 else rng.uniform(-400,400)) for i in range(n));alpha=rng.choice((0.,.5,1.,rng.random()));pa=tuple((rng.uniform(-1,1),rng.uniform(-1,1)) for i in range(n));pb=tuple((rng.uniform(-1,1),rng.uniform(-1,1)) for i in range(n));ra=rng.uniform(-5,5);rb=rng.uniform(-5,5)
  p=(C.c_double*(2*n))(*(v for pt in points for v in pt));a=(C.c_double*(2*n))(*(v for pt in pa for v in pt));b=(C.c_double*(2*n))(*(v for pt in pb for v in pt));off=(C.c_uint32*2)(0,n);ids=(C.c_uint32*n)(*range(n));ars=(C.c_double*1)(ra);brs=(C.c_double*1)(rb);rectangle=(C.c_double*4)(*rect);f=(C.c_uint8*1)(91);code=(C.c_uint8*1)(92)
  assert _classify(p,n,off,ids,1,n,ars,brs,a,b,alpha,rectangle,f,code)==0
  expected=determinant(points)+(1-alpha)*ra+alpha*rb>-.5;corrected=tuple(tuple(v+(1-alpha)*x+alpha*y for v,x,y in zip(pt,xs,ys)) for pt,xs,ys in zip(points,pa,pb))
  assert bool(f[0])==expected and code[0]==source_rectangle_classify(corrected,tuple(range(n)),rect);checks+=1
threshold_cases=0
for det in (math.nextafter(-.5,-math.inf),-.5,math.nextafter(-.5,math.inf),-1.,0.,1.):
 pts=(C.c_double*6)(0,0,0,1,det,0);zero=(C.c_double*6)();res=(C.c_double*1)();of=(C.c_uint32*2)(0,3);ix=(C.c_uint32*3)(0,1,2);fo=(C.c_uint8*1)();co=(C.c_uint8*1)()
 for fraction in (0.,.5,1.):
  assert _classify(pts,3,of,ix,1,3,res,res,zero,zero,fraction,rectangle,fo,co)==0
  assert bool(fo[0])==(det>-.5);threshold_cases+=1
# Reuse last valid arrays; each invalid input must reject before any output write.
invalid=[]
def bad(label,**changes):
 args=[p,n,off,ids,1,n,ars,brs,a,b,alpha,rectangle,f,code]
 for position,value in changes.items():args[int(position)]=value
 f[0]=91;code[0]=92;assert _classify(*args)==1 and (f[0],code[0])==(91,92);invalid.append(label)
for value in (float('nan'),float('inf'),-.1,1.1):bad('alpha',**{'10':value})
bad('null points',**{'0':None});bad('zero vertices',**{'1':0});bad('oversize vertices',**{'1':65537});bad('oversize faces',**{'4':32769});bad('oversize indices',**{'5':1048577})
for buffer,index,value,label in ((p,0,float('nan'),'point nan'),(a,0,float('inf'),'residual inf'),(ars,0,float('nan'),'face residual nan'),(rectangle,0,float('inf'),'rect inf'),(off,0,1,'offset start'),(off,1,2,'short face'),(ids,0,n,'index range')):
 old=buffer[index];buffer[index]=value;bad(label);buffer[index]=old
out=dict(result='PASS',exact_boundary_random_cases=checks,invalid_cases=len(invalid),exact_threshold_cases=threshold_cases,output_unchanged_on_rejection=True,scope='Native face sizes3..32,edge-adjacent points,fractions andinvalidinputs; buffers remain correctly sized by caller');Path('work/camera/source-classify-boundary-tests.json').write_text(json.dumps(out,indent=2));print(out)
