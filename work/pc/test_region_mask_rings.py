from pathlib import Path
import os,ctypes as C,json,hashlib,zlib,struct,math,collections,threading
import numpy as np
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-region-mask-tests'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
build=json.loads((out/'region-build-report.json').read_text());assert sha(out/'recipe-regions.dll')==build['dll_sha256']
for p,h in build['source_sha256'].items():assert sha(p)==h,p
# Receipt-checked archive maps plus independent physical-plane fit.
audit=here/'audit_recipe_footprint.py';ns={'__file__':str(audit),'__name__':'region_inputs'};exec(compile(audit.read_text(),str(audit),'exec'),ns)
P=ns['P'];S=ns['S'];Q=ns['Q'];U=ns['U'];D=ns['D'];fn=ns['scope']['fn'];make=ns['make'];inside=ns['inside']
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'recipe-regions.dll'))
cover=fn(d,'nf_pc_recipe_coverage_decode',[P,S,P,S,P,U,U,U,S],P);cf=fn(d,'nf_pc_recipe_coverage_free',[P],None);cbuffer=fn(d,'nf_pc_recipe_coverage_buffer',[P,U,P,P]);create=fn(d,'nf_pc_recipe_regions_create',[P,S],P);free=fn(d,'nf_pc_recipe_regions_free',[P],None);info=fn(d,'nf_pc_recipe_regions_info',[P,P]);buffer=fn(d,'nf_pc_recipe_regions_buffer',[P,P,P]);ring=fn(d,'nf_pc_recipe_region_mask_ring',[P,S,P,P,P,P,P,D,P,P,S,P]);gd=fn(d,'nf_pc_recipe_geometry_decode',[Q,U,U,P,U,S],P);gf=fn(d,'nf_pc_recipe_geometry_free',[P],None);fc=fn(d,'nf_pc_recipe_footprint_create',[P,Q,U,P,S],P);ff=fn(d,'nf_pc_recipe_footprint_free',[P],None);mesh=fn(d,'nf_pc_recipe_mesh_ring',[P,U,S],P);mf=fn(d,'nf_pc_recipe_mesh_free',[P],None);minfo=fn(d,'nf_pc_recipe_mesh_info',[P,P])
def blob(func,*args):p=P();n=S();assert func(*args,C.byref(p),C.byref(n));return C.string_at(p,n.value) if n.value else b''
pair=json.loads((base/'NFSUG-pc-recipe-mesh-tests/camera-pair.json').read_text());a=pair['older'];b=pair['newer'];pa=np.array(pair['older_pose']);pb=np.array(pair['newer_pose']);A=(Q*5)(*a);B=(Q*5)(*b);CA=(D*7)(*pa);CB=(D*7)(*pb);projection=(D*3)(*pair['projection'])
def matrix(q):
 x,y,z,s=q/np.linalg.norm(q);return np.array([[1-2*(y*y+z*z),2*(x*y-z*s),2*(x*z+y*s)],[2*(x*y+z*s),1-2*(x*x+z*z),2*(y*z-x*s)],[2*(x*z-y*s),2*(y*z+x*s),1-2*(x*x+y*y)]])
def pose(alpha):
 qa=pa[3:]/np.linalg.norm(pa[3:]);qb=pb[3:]/np.linalg.norm(pb[3:]);dot=float(qa@qb)
 if dot<0:qb=-qb;dot=-dot
 if dot>.9995:q=(1-alpha)*qa+alpha*qb;q/=np.linalg.norm(q)
 else:t=math.acos(min(1.,dot));q=(math.sin((1-alpha)*t)*qa+math.sin(alpha*t)*qb)/math.sin(t)
 return (1-alpha)*pa[:3]+alpha*pb[:3],matrix(q)
def clip_project(camera,current_position,current_rotation,owner_position,owner_rotation):
 clipped=[]
 for i,y in enumerate(camera):
  x=camera[i-1];xi=x[2]>=64;yi=y[2]>=64
  if xi!=yi:t=(64-x[2])/(y[2]-x[2]);z=x+t*(y-x);z[2]=64;clipped.append(z)
  if yi:clipped.append(y)
 if not clipped:return np.empty((0,6))
 p=np.array(clipped);world=p@current_rotation+current_position;old=(world-owner_position)@owner_rotation.T;return np.column_stack([120+128*p[:,0]/p[:,2],87+128*p[:,1]/p[:,2],p[:,2],120+128*old[:,0]/old[:,2],87+128*old[:,1]/old[:,2],old[:,2]/p[:,2]])
coverage=base/'NFSUG-pc-recipe-coverage-tests';cr=json.loads((coverage/'coverage-test-report.json').read_text());region_cases=rectangles=cells=ring_samples=triangle_vertices=endpoint_points=fractional_digests=negative=0;max_error=0.;rows=[];held=[];synthetic=None
for name,h in cr['fixture_sha256'].items():
 assert sha(coverage/name)==h;raw=zlib.decompress((coverage/name).read_bytes()[8:]);fields=struct.unpack_from('<5Q4I',raw);key=(Q*5)(*fields[:5]);kind,top,bottom,hn=fields[5:];history=raw[56:56+hn];proof=raw[56+hn:];c=cover(history,len(history),proof,len(proof),key,kind,top,bottom,64*1024*1024);assert c;records=np.frombuffer(blob(cbuffer,c,2),'<u8').reshape(-1,6).copy();regions=create(c,64*1024*1024);assert regions;meta=(Q*9)();assert info(regions,meta) and list(meta[:6])==list(key)+[kind] and meta[6]==len(records);packed=blob(buffer,regions);rects=np.frombuffer(packed,'<u8').reshape(-1,8).copy();assert len(rects)==meta[7]
 if negative==0:
  assert not create(c,meta[8]-1);exact=create(c,meta[8]);assert exact;free(exact);assert not create(None,64*1024*1024);negative+=2
 cf(c)
 # Independently reconstruct the complete labelled bitmap; no overlaps or lost holes.
 expected=np.zeros(38400,np.uint64);expected[records[:,0].astype(int)]=records[:,3];actual=np.zeros((160,240),np.uint64)
 for v in rects:
  epoch,rkind,ordinal,refresh,l,r,t,bt=map(int,v);assert epoch==key[0] and rkind==kind-1 and 0<=l<r<=240 and top<=t<bt<=bottom;assert not actual[t:bt,l:r].any();actual[t:bt,l:r]=ordinal
 assert np.array_equal(actual.ravel(),expected);assert sum((int(v[5])-int(v[4]))*(int(v[7])-int(v[6])) for v in rects)==len(records);region_cases+=1;cells+=len(records);rectangles+=len(rects);footprints={};worldcache={};endpoint_mask=np.zeros((160,240),np.uint64)
 try:
  for ri,v in enumerate(rects):
   epoch,rkind,ordinal,refresh,l,r,t,bt=map(int,v)
   if ordinal not in footprints:
    item=(ns['roadmap'] if kind==2 else ns['wallmap'])[ordinal];keep,bs=make(item['blocks'][:12]);geometry=gd(epoch,item['refresh'],rkind,bs,12,65536);assert geometry;f=fc(geometry,ordinal,refresh,projection,65536);assert f;gf(geometry);footprints[ordinal]=f;worldcache[ordinal]=ns['cache'][(rkind,item['identity'])]
   f=footprints[ordinal];world,centroid,basis,normal,deviation,rawR,translation=worldcache[ordinal];owner_alpha=0 if list(key)==a else 1;owner=pa if owner_alpha==0 else pb;R=matrix(owner[3:]);xy=np.array([[l,t],[r,t],[r,bt],[l,bt]],float);rays=np.column_stack([(xy[:,0]-120)/128,(xy[:,1]-87)/128,np.ones(4)]);direction=rays@R;depth=np.dot(centroid-owner[:3],normal)/(direction@normal);assert (depth>0).all();points=owner[:3]+direction*depth[:,None];digests=[]
   for alpha in ([0.,.25,.5,.75,1.] if owner_alpha==0 else [1.]):
    pos,rotation=pose(alpha);reference=clip_project((points-pos)@rotation.T,pos,rotation,owner[:3],R);output=(D*36)();n=U(777);assert ring(regions,ri,f,A,CA,B,CB,alpha,projection,output,C.sizeof(output),C.byref(n));got=np.array(output[:n.value*6]).reshape(-1,6);assert got.shape==reference.shape;error=float(np.max(np.abs(got-reference))) if len(got) else 0.;max_error=max(max_error,error);assert error<1e-6,(ri,alpha,error);ring_samples+=1;digests.append(hashlib.sha256(got.tobytes()).hexdigest())
    m=mesh(output,n.value,65536);assert m;mi=(Q*3)();assert minfo(m,mi);triangle_vertices+=mi[1];mf(m)
    if alpha==owner_alpha:
     yy,xx=np.indices((bt-t,r-l));pixels=np.column_stack([xx.ravel()+l+.5,yy.ravel()+t+.5]);mask=inside(pixels,got[:,:2]);assert mask.all(),('Endpoint lost original cells',ri,int(np.count_nonzero(~mask)));
     # Also test a one-cell guard band to detect spurious endpoint coverage.
     xlo=max(0,l-1);xhi=min(240,r+1);ylo=max(0,t-1);yhi=min(160,bt+1);yy,xx=np.indices((yhi-ylo,xhi-xlo));pixels=np.column_stack([xx.ravel()+xlo+.5,yy.ravel()+ylo+.5]);covered=inside(pixels,got[:,:2]);wanted=(pixels[:,0]>=l)&(pixels[:,0]<r)&(pixels[:,1]>=t)&(pixels[:,1]<bt);assert np.array_equal(covered,wanted);endpoint_points+=len(pixels);endpoint_mask[t:bt,l:r]=ordinal
   if len(digests)==5:assert all(h not in [digests[0],digests[-1]] for h in digests[1:-1]);fractional_digests+=3
   if synthetic is None and owner_alpha==0 and np.ptp(points[:,2])>1e-6:synthetic=(regions,ri,f,points.copy())
   if ri==0:
    for cap,alpha,index in [(287,owner_alpha,ri),(288,-1.,ri),(288,owner_alpha,len(rects))]:sentinel=C.create_string_buffer(b'\xa5'*288);n=U(777);assert not ring(regions,index,f,A,CA,B,CB,alpha,projection,sentinel,cap,C.byref(n)) and n.value==777 and sentinel.raw==b'\xa5'*288+b'\0';negative+=1
    if owner_alpha==1:sentinel=C.create_string_buffer(b'\xa5'*288);n=U(777);assert not ring(regions,ri,f,A,CA,B,CB,.5,projection,sentinel,288,C.byref(n)) and n.value==777 and sentinel.raw==b'\xa5'*288+b'\0';negative+=1
  assert np.array_equal(endpoint_mask.ravel(),expected)
  # Keep source-independent objects for near-plane and worker lifetime checks.
  held.append((regions,dict(footprints),hashlib.sha256(packed).hexdigest()));regions=None;footprints={}
  rows.append(dict(owner=list(key),kind=kind,cells=len(records),rectangles=len(rects),retained_bytes=meta[8]))
 finally:
  for f in footprints.values():ff(f)
  if regions:free(regions)
assert synthetic
regions,ri,f,points=synthetic;quaternion=np.array([.13,.27,.07,.95]);quaternion/=np.linalg.norm(quaternion);R=matrix(quaternion);initial=(points-pa[:3])@R.T;z=sorted(initial[:,2]);assert min(np.diff(z))>1e-6;cutoffs=[z[0]-128]+[(z[i]+z[i+1])/2-64 for i in range(3)]+[z[-1]+128];near_counts=collections.Counter()
for shift in cutoffs:
 position=pa[:3]+np.array([0,0,shift])@R;newpose=(D*7)(*position,*quaternion);reference=clip_project((points-position)@R.T,position,R,pa[:3],matrix(pa[3:]));output=(D*36)();n=U(777);assert ring(regions,ri,f,A,CA,B,newpose,1.,projection,output,C.sizeof(output),C.byref(n));got=np.array(output[:n.value*6]).reshape(-1,6);assert got.shape==reference.shape and np.allclose(got,reference,rtol=0,atol=1e-6);near_counts[str(n.value)]+=1;m=mesh(output,n.value,65536);assert m;mf(m)
assert all(str(n) in near_counts for n in [0,3,4,5])
worker_result=[]
def worker():
 for regions,footprints,wanted in held:
  assert hashlib.sha256(blob(buffer,regions)).hexdigest()==wanted
  for f in footprints.values():ff(f)
  free(regions)
 worker_result.append(True)
t=threading.Thread(target=worker);t.start();t.join();assert worker_result==[True]
r=dict(result='PASS_PROJECTIVE_OWNER_COORDINATES_AND_NEAR_CLIPPED_MASK_RINGS',owner_layer_cases=region_cases,cells=cells,rectangles=rectangles,ring_samples=ring_samples,triangle_vertices=triangle_vertices,endpoint_center_and_guard_points=endpoint_points,fractional_ring_digests_different_from_both_endpoints=fractional_digests,maximum_independent_ring_error=max_error,synthetic_near_clip_vertex_counts=dict(near_counts),negative_requests_preserve_output_and_count=negative,original_labelled_coverage_masks_exact=True,no_overlaps_or_lost_holes=True,owned_after_coverage_free_and_worker_release=True,dll_sha256=sha(out/'recipe-regions.dll'),build_report_sha256=sha(out/'region-build-report.json'),audit_report_sha256=sha(base/'NFSUG-pc-recipe-footprint-tests/footprint-audit-report.json'),coverage_report_sha256=sha(coverage/'coverage-test-report.json'),script_sha256=sha(Path(__file__)),rows=rows,scope='Exact source-writer coverage partition and CPU world-anchored near-clipped geometry. Owner-screen projective coordinates are independently checked; no game material indices, GPU composition, occlusion/order or live timing verified.',core_opened=False,gpu_drawn=False,full_scene_60fps=False)
(out/'mask-ring-test-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='rows'},indent=2))
