from pathlib import Path
import json,ctypes as C,hashlib,zlib,struct,threading,math
import numpy as np
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-recipe-footprint-tests'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
build=json.loads((out/'footprint-build-report.json').read_text());assert sha(out/'recipe-footprint.dll')==build['dll_sha256']
for p,h in build['source_sha256'].items():assert sha(p)==h,p
# Reuse the authoritative archive/coverage audit inputs and independent plane fit.
audit=here/'audit_recipe_footprint.py';ns={'__file__':str(audit),'__name__':'footprint_audit'};exec(compile(audit.read_text(),str(audit),'exec'),ns)
P=ns['P'];S=ns['S'];Q=ns['Q'];U=ns['U'];D=ns['D'];fn=ns['scope']['fn'];make=ns['make']
with __import__('os').add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'recipe-footprint.dll'))
decode=fn(d,'nf_pc_recipe_geometry_decode',[Q,U,U,P,U,S],P);gf=fn(d,'nf_pc_recipe_geometry_free',[P],None);create=fn(d,'nf_pc_recipe_footprint_create',[P,Q,U,P,S],P);free=fn(d,'nf_pc_recipe_footprint_free',[P],None);info=fn(d,'nf_pc_recipe_footprint_info',[P,P]);lift=fn(d,'nf_pc_recipe_footprint_lift',[P,D,D,P]);source=fn(d,'nf_pc_recipe_footprint_source',[P,P,P]);sample=fn(d,'nf_pc_recipe_footprint_sample',[P,P,P,P,P,D,D,D,P]);liftpose=fn(d,'nf_pc_recipe_footprint_lift_pose',[P,P,D,D,P]);anchored=fn(d,'nf_pc_recipe_footprint_sample_anchored',[P,P,P,P,P,P,D,D,D,P])
pair=json.loads((base/'NFSUG-pc-recipe-mesh-tests/camera-pair.json').read_text());a=pair['older'];b=pair['newer'];pa=np.array(pair['older_pose']);pb=np.array(pair['newer_pose']);A=(Q*5)(*a);B=(Q*5)(*b);CA=(D*7)(*pa);CB=(D*7)(*pb);projection=(D*3)(*pair['projection'])
def rigid(points,alpha):
 qa=pa[3:]/np.linalg.norm(pa[3:]);qb=pb[3:]/np.linalg.norm(pb[3:]);dot=float(qa@qb)
 if dot<0:qb=-qb;dot=-dot
 if dot>.9995:q=(1-alpha)*qa+alpha*qb;q/=np.linalg.norm(q)
 else:angle=math.acos(min(1.,dot));q=(math.sin((1-alpha)*angle)*qa+math.sin(alpha*angle)*qb)/math.sin(angle)
 x,y,z,s=q;R=np.array([[1-2*(y*y+z*z),2*(x*y-z*s),2*(x*z+y*s)],[2*(x*y+z*s),1-2*(x*x+z*z),2*(y*z-x*s)],[2*(x*z-y*s),2*(y*z+x*s),1-2*(x*x+y*y)]])
 return (points-((1-alpha)*pa[:3]+alpha*pb[:3]))@R.T
coverage=base/'NFSUG-pc-recipe-coverage-tests';cr=json.loads((coverage/'coverage-test-report.json').read_text());cells=points_checked=camera_samples=temporally_excluded=guards=0;max_world=max_source=max_camera=0.;changed=0;held=None;cases=[];anchored_points=anchored_samples=anchored_motion=unliftable_anchor_points=0;max_anchor_world=max_anchor_endpoint=max_anchor_camera=0.;source_anchor_endpoint_shifts=[]
for name,h in cr['fixture_sha256'].items():
 assert sha(coverage/name)==h;raw=zlib.decompress((coverage/name).read_bytes()[8:]);fields=struct.unpack_from('<5Q4I',raw);key=(Q*5)(*fields[:5]);kind,top,bottom,hn=fields[5:];history=raw[56:56+hn];proof=raw[56+hn:];cover=ns['f'](history,len(history),proof,len(proof),key,kind,top,bottom,64*1024*1024);assert cover;ptr=P();size=S();assert ns['get'](cover,2,C.byref(ptr),C.byref(size));data=np.frombuffer(C.string_at(ptr,size.value),'<u8').reshape(-1,6).copy();ns['fr'](cover)
 for ordinal in sorted(set(map(int,data[:,3]))):
  r=(ns['roadmap'] if kind==2 else ns['wallmap'])[ordinal];subset=data[data[:,3]==ordinal];write=int(subset[0,4]);assert (subset[:,4]==write).all();keep,bs=make(r['blocks'][:12]);geometry=decode(r['epoch'],r['refresh'],r['kind'],bs,12,65536);assert geometry;f=create(geometry,ordinal,write,projection,65536);assert f;gf(geometry)
  mi=(Q*6)();assert info(f,mi) and list(mi[:5])==[key[0],kind-1,ordinal,r['refresh'],write]
  # Entire input geometry and source bytes are gone before footprint sampling.
  for buf in keep:C.memset(buf,0,len(buf))
  world,centroid,basis,normal,deviation,R,t=ns['cache'][(r['kind'],r['identity'])];xy=np.column_stack([subset[:,0]%240+.5,subset[:,0]//240+.5]);allxy=np.concatenate([xy]+[xy+offset for offset in [[-.5,-.5],[.5,-.5],[.5,.5],[-.5,.5]]]);rays=np.column_stack([(allxy[:,0]-120)/128,(allxy[:,1]-87)/128,np.ones(len(allxy))]);directions=rays@np.linalg.inv(R).T;den=directions@normal;depth=np.dot(centroid+t,normal)/den;valid=np.isfinite(depth)&(depth>0)&(np.abs(den)>1e-12);wanted=-t+directions[valid]*depth[valid,None];actual=[]
  for (x,y),ok in zip(allxy,valid):
   result=(D*4)(*[987.]*4);accepted=lift(f,x,y,result);assert bool(accepted)==bool(ok)
   if not ok:assert list(result)==[987.]*4;continue
   actual.append(list(result[:3]));projected=(D*3)();assert source(f,result,projected);max_source=max(max_source,abs(projected[0]-x),abs(projected[1]-y))
  actual=np.array(actual);error=float(np.max(np.abs(actual-wanted)));max_world=max(max_world,error);assert error<1e-7 and max_source<1e-7;points_checked+=int(valid.sum());cells+=len(subset);digests=[]
  for alpha in [0.,.5,1.]:
   if write>(b[3] if alpha==1 else a[3]):temporally_excluded+=len(xy);sentinel=(D*3)(987,987,987);assert not sample(f,A,CA,B,CB,alpha,*xy[0],sentinel) and list(sentinel)==[987]*3;continue
   results=[]
   for x,y in xy:
    result=(D*3)();assert sample(f,A,CA,B,CB,alpha,x,y,result);results.append(list(result))
   results=np.array(results);reference=rigid(wanted[:len(xy)],alpha);assert len(results)==len(xy);error=float(np.max(np.abs(results-reference)));max_camera=max(max_camera,error);assert error<1e-7;camera_samples+=len(xy);digests.append(hashlib.sha256(results.tobytes()).hexdigest())
  if len(digests)==3:assert len(set(digests))==3;changed+=len(xy)
  # Anchor exact displayed coverage at its owner endpoint, not writer camera.
  owner_alpha=0. if list(key)==a else 1.;owner_pose=CA if owner_alpha==0 else CB;owner_position=pa[:3] if owner_alpha==0 else pb[:3];M=rigid(np.eye(3),owner_alpha)-rigid(np.zeros((1,3)),owner_alpha);directions=rays@M.T;den=directions@normal;adepth=np.dot(centroid-owner_position,normal)/den;avalid=np.isfinite(adepth)&(adepth>0)&(np.abs(den)>1e-12);awanted=owner_position+directions[avalid]*adepth[avalid,None];agotten=[]
  for (x,y),ok in zip(allxy,avalid):
   result=(D*4)(987,987,987,987);accepted=liftpose(f,owner_pose,x,y,result);assert bool(accepted)==bool(ok)
   if ok:agotten.append(list(result[:3]))
   else:assert list(result)==[987]*4;unliftable_anchor_points+=1
  agotten=np.array(agotten);error=float(np.max(np.abs(agotten-awanted))) if len(agotten) else 0.;max_anchor_world=max(max_anchor_world,error);assert error<1e-7;anchored_points+=int(avalid.sum());assert avalid[:len(xy)].all()
  old_view=rigid(wanted[:len(xy)],owner_alpha);old_projection=np.column_stack([120+128*old_view[:,0]/old_view[:,2],87+128*old_view[:,1]/old_view[:,2]]);source_anchor_endpoint_shifts.extend(np.max(np.abs(old_projection-xy),axis=1).tolist())
  adigests=[]
  for alpha in ([0.,.5,1.] if owner_alpha==0 else [1.]):
   results=[]
   for x,y in xy:
    result=(D*3)();assert anchored(f,key,A,CA,B,CB,alpha,x,y,result);results.append(list(result))
   results=np.array(results);reference=rigid(awanted[:len(xy)],alpha);error=float(np.max(np.abs(results-reference)));max_anchor_camera=max(max_anchor_camera,error);assert error<1e-7;anchored_samples+=len(xy);adigests.append(hashlib.sha256(results.tobytes()).hexdigest())
   if alpha==owner_alpha:
    projected=np.column_stack([120+128*results[:,0]/results[:,2],87+128*results[:,1]/results[:,2]]);error=float(np.max(np.abs(projected-xy)));max_anchor_endpoint=max(max_anchor_endpoint,error);assert error<1e-7
  if len(adigests)==3:assert len(set(adigests))==3;anchored_motion+=len(xy)
  if owner_alpha==1:
   for alpha in [0.,.5]:sentinel=(D*3)(987,987,987);assert not anchored(f,key,A,CA,B,CB,alpha,*xy[0],sentinel) and list(sentinel)==[987]*3;guards+=1
  if held is None:
   assert not create(None,ordinal,write,projection,65536);guards+=1
   # Recreate geometry to test allocation and invalid source plane guards.
   original_keep,original_bs=make(r['blocks'][:12]);geometry=decode(r['epoch'],r['refresh'],r['kind'],original_bs,12,65536);assert geometry;assert not create(geometry,ordinal,write,projection,mi[5]-1);exact=create(geometry,ordinal,write,projection,mi[5]);assert exact;free(exact);assert not create(geometry,0,write,projection,65536);guards+=2
   assert not create(geometry,ordinal,r['refresh']-1,projection,65536);guards+=1
   late=create(geometry,ordinal,a[3]+1,projection,65536);assert late
   for alpha in [0.,.5]:sentinel=(D*3)(987,987,987);assert not sample(late,A,CA,B,CB,alpha,*xy[0],sentinel) and list(sentinel)==[987]*3;guards+=1
   result=(D*3)();assert sample(late,A,CA,B,CB,1,*xy[0],result);free(late);gf(geometry)
   for x,y in [(float('nan'),0),(0,float('inf'))]:sentinel=(D*4)(987,987,987,987);assert not lift(f,x,y,sentinel) and list(sentinel)==[987]*4;guards+=1
   # A source ray parallel to the support plane must reject atomically.
   camera_normal=np.linalg.inv(R).T@normal
   if abs(camera_normal[1])>1e-8:parallel=(120.,87.-128*camera_normal[2]/camera_normal[1])
   else:parallel=(120.-128*camera_normal[2]/camera_normal[0],87.)
   sentinel=(D*4)(987,987,987,987);assert not lift(f,*parallel,sentinel) and list(sentinel)==[987]*4;guards+=1
   for badalpha in [-1.,2.,float('nan')]:sentinel=(D*3)(987,987,987);assert not sample(f,A,CA,B,CB,badalpha,*xy[0],sentinel) and list(sentinel)==[987]*3;guards+=1
   for field in [0,1,4]:bad=(Q*5)(*b);bad[field]=a[0]+1 if field==0 else a[1] if field==1 else 2;sentinel=(D*3)(987,987,987);assert not sample(f,A,CA,bad,CB,.5,*xy[0],sentinel) and list(sentinel)==[987]*3;guards+=1
   zero_pose=(D*7)(*pa[:3],0,0,0,0);sentinel=(D*3)(987,987,987);assert not sample(f,A,zero_pose,B,CB,.5,*xy[0],sentinel) and list(sentinel)==[987]*3;guards+=1
   held=(f,tuple(xy[0]),tuple(wanted[0]));f=None
  if f:free(f)
  cases.append(dict(kind=kind-1,ordinal=ordinal,cells=len(subset),valid_center_and_corner_points=int(valid.sum()),accepted_write_refresh=write,source_capture_refresh=r['refresh']))
# An immutable footprint can be read and released on another thread.
worker_result=[]
def worker():
 f,xy,want=held;result=(D*4)();assert lift(f,*xy,result) and np.allclose(result[:3],want,rtol=0,atol=1e-7);free(f);worker_result.append(True)
thread=threading.Thread(target=worker);thread.start();thread.join();assert worker_result==[True]
# Malformed source matrix and nonplanar road geometry reject at construction.
road=next(r for r in ns['records'] if r['kind']==1 and len(r['blocks'][0])>=4*68)
for mode in ['singular','nonplanar']:
 values=list(road['blocks'][:12])
 if mode=='singular':values[4]=bytes(48)
 else:v=bytearray(values[0]);old=struct.unpack_from('<h',v,56)[0];struct.pack_into('<h',v,56,old+13);values[0]=bytes(v)
 keep,bs=make(values);geometry=decode(road['epoch'],road['refresh'],1,bs,12,65536);assert geometry;assert not create(geometry,1,road['refresh'],projection,65536),mode;gf(geometry);guards+=1
report=dict(result='PASS_OWNED_SOURCE_PLANE_LIFT_AND_RIGID_CAMERA_COMPONENT',writer_cases=len(cases),retained_centers=cells,center_and_corner_points=points_checked,camera_samples=camera_samples,newer_write_samples_excluded=temporally_excluded,centers_with_three_distinct_camera_samples=changed,max_independent_world_error=max_world,max_continuous_source_roundtrip_error=max_source,max_independent_rigid_camera_error=max_camera,negative_and_temporal_guards=guards,owned_after_geometry_and_input_overwrite=True,worker_read_free=True,source_capture_and_write_timing_separate=True,dll_sha256=sha(out/'recipe-footprint.dll'),build_report_sha256=sha(out/'footprint-build-report.json'),audit_report_sha256=sha(out/'footprint-audit-report.json'),script_sha256=sha(Path(__file__)),cases=cases,owner_anchored_center_and_corner_points=anchored_points,owner_anchored_camera_samples=anchored_samples,owner_anchored_centers_with_three_distinct_samples=anchored_motion,owner_anchor_unliftable_points=unliftable_anchor_points,max_owner_anchor_world_error=max_anchor_world,max_owner_anchor_endpoint_reprojection_error=max_anchor_endpoint,max_owner_anchor_camera_error=max_anchor_camera,writer_camera_anchor_endpoint_shift_median=float(np.median(source_anchor_endpoint_shifts)),writer_camera_anchor_endpoint_shift_maximum=float(np.max(source_anchor_endpoint_shifts)),writer_camera_anchor_cells_shifted_over_half_pixel=int(np.count_nonzero(np.array(source_anchor_endpoint_shifts)>.5)),scope='Actual retained cell centers/corners lifted to source supporting planes then sampled with common rigid camera. Continuous raw-camera roundtrip is not original integer projection/UV or final occlusion/coverage compositing. Does not clip quantized border cells to ideal polygon.',core_opened=False,gpu_drawn=False,full_scene_60fps=False)
(out/'footprint-test-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2))
