from pathlib import Path
import os,ctypes as C,json,hashlib,struct,zlib,math
import numpy as np
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-recipe-geometry-tests'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((out/'geometry-build-report.json').read_text());assert sha(out/'recipe-geometry.dll')==build['dll_sha256']
for path,h in build['source_sha256'].items():assert sha(Path(path))==h
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'recipe-geometry.dll'));core=C.CDLL(str(base/'NFSUG-pc-recipe-runtime-tests/capture-host.dll'));reader=C.CDLL(str(base/'NFSUG-pc-reader-tests/source-reader.dll'));baseline=C.CDLL(str(base/'NFSUG-pc-world-mesh-motion-tests/world-mesh-motion.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint;I=C.c_int
class Block(C.Structure):_fields_=[('data',P),('bytes',S)]
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
def fn(lib,n,args,r=I):f=getattr(lib,n);f.argtypes=args;f.restype=r;return f
op=fn(core,'nfa_core_open',[C.c_char_p],P);close=fn(core,'nfa_core_close',[P],None);load=fn(core,'nfa_core_load_state',[P,P,S]);step=fn(core,'nfa_core_step',[P,U]);pixels=fn(core,'nfa_core_pixels',[P],P);audio=fn(core,'nfa_core_read_audio',[P,P,S],S);timing=fn(core,'nfa_core_timing',[P,P]);bind=fn(reader,'nf_pc_source_api_bind_owner',[P]);ro=fn(reader,'nf_pc_source_reader_open',[P,S],P);rcap=fn(reader,'nf_pc_source_reader_capture',[P,S],P);rc=fn(reader,'nf_pc_source_reader_close',[P],None);fi=fn(reader,'nf_pc_source_frame_info',[P,P]);oi=fn(reader,'nf_pc_source_frame_owner',[P,U,P]);component=fn(reader,'nf_pc_source_frame_component',[P,U,U,P,P]);ff=fn(reader,'nf_pc_source_frame_free',[P],None)
decode=fn(d,'nf_pc_recipe_geometry_decode',[Q,U,U,P,U,S],P);free=fn(d,'nf_pc_recipe_geometry_free',[P],None);info=fn(d,'nf_pc_recipe_geometry_info',[P,P]);buffer=fn(d,'nf_pc_recipe_geometry_buffer',[P,U,P,P]);camera=fn(d,'nf_pc_recipe_geometry_camera',[P,P,P,P,P,C.c_double,P,S]);project=fn(d,'nf_pc_recipe_geometry_project',[P,P,P,P,P,C.c_double,P,P,S,P,S,P]);old_road=fn(core,'nf_road_source_decode',[P,S,P,S,P,P,U,U,P,P]);old_wall=fn(core,'nf_wall_owned_quad',[P,P,P,P]);old_clip=fn(baseline,'nf_pc_road_clip',[P,P,U,P,S,P,P])
for n in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TEST_DIRECT_CAPTURE_ROM']:os.environ.pop(n,None)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';before={str(p):sha(p) for p in [rom,state]};data=state.read_bytes();h=op(os.fsencode(rom));assert h and load(h,data,len(data))
for n in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn(core,'nfa_core_'+n,[P,I])(h,1)
api=API(C.sizeof(API),h,*[C.cast(getattr(core,'nfa_core_'+n),P).value for n in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert bind(C.byref(api));r=ro(C.byref(api),64*1024*1024);assert r;initial=(Q*4)();assert timing(h,initial);pcm=(C.c_int16*8192)();digest=hashlib.sha256();samples=0;views={}
try:
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for i in range(600):
   assert step(h,1|(16 if 60<=i<120 else 0)|(32 if 480<=i<540 else 0))==1 and C.string_at(pixels(h),153600)==oracle.read(153600);tick=(Q*4)();assert timing(h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==initial[2]+i+1 and tick[3]==i+1
   while True:
    n=audio(h,pcm,4096)
    if not n:break
    samples+=n;digest.update(C.string_at(pcm,n*4))
   if i<580:continue
   frame=rcap(r,64*1024*1024);assert frame;meta=(Q*8)();assert fi(frame,meta)
   for owner in range(meta[4]):
    key=(Q*5)();assert oi(frame,owner,key);p=P();n=S();assert component(frame,owner,1,C.byref(p),C.byref(n));packet=C.string_at(p,n.value);model=struct.unpack_from('<I',packet,36)[0]
    if struct.unpack_from('<I',packet,model)[0]==0x314c4d4e:model+=struct.unpack_from('<I',packet,model+8)[0]
    assert struct.unpack_from('<I',packet,model)[0]==0x324d464e;views[tuple(key)]=(struct.unpack_from('<7d',packet,model+48),struct.unpack_from('<3d',packet,model+24))
   ff(frame)
finally:rc(r);close(h)
assert samples==443007 and digest.hexdigest()=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e'
a,b=sorted(views,key=lambda k:k[1])[-2:];pa,projection=views[a];pb,_=views[b];assert a[0]==b[0] and 0<b[3]-a[3]<=8
(out/'camera-pair.json').write_text(json.dumps(dict(older=a,newer=b,older_pose=pa,newer_pose=pb,projection=projection),indent=2))
A=(Q*5)(*a);B=(Q*5)(*b);CA=(C.c_double*7)(*pa);CB=(C.c_double*7)(*pb);proj=(C.c_double*3)(*projection)
road_dir=base/'NFSUG-pc-road-recipe-tests';wall_dir=base/'NFSUG-pc-wall-lineage-tests';rr=json.loads((road_dir/'recipe-test-report.json').read_text());wr=json.loads((wall_dir/'lineage-test-report.json').read_text());assert sha(road_dir/'road-source-recipes.nrrz')==rr['archive_sha256'] and sha(wall_dir/'wall-source-lineage.wclz')==wr['archive_sha256'];table=(road_dir/'source-reciprocals.bin').read_bytes();records=[]
raw=(road_dir/'road-source-recipes.nrrz').read_bytes();at=8
while at<len(raw):
 n=struct.unpack_from('<I',raw,at)[0];at+=4;record=zlib.decompress(raw[at:at+n]);at+=n;header=struct.unpack_from('<10Q',record);pos=80+header[5]*68;blocks=[]
 for j in range(12):n=struct.unpack_from('<I',record,pos)[0];pos+=4;blocks.append(record[pos:pos+n]);pos+=n
 records.append((1,header[2],header[3],blocks))
raw=(wall_dir/'wall-source-lineage.wclz').read_bytes();at=8
while at<len(raw):
 n=struct.unpack_from('<I',raw,at)[0];at+=4;blob=zlib.decompress(raw[at:at+n]);at+=n;pos=0
 while pos<len(blob):
  tag,n,epoch,refresh,call=struct.unpack_from('<5Q',blob,pos);record=blob[pos:pos+n]
  if tag==2:
   cursor=64;blocks=[]
   for j in range(12):size=struct.unpack_from('<I',record,cursor)[0];cursor+=4;blocks.append(record[cursor:cursor+size]);cursor+=size
   records.append((2,epoch,refresh,blocks))
  pos+=n
assert len(records)==rr['records']+wr['owned_source_recipes']
def h(data,at):return struct.unpack_from('<h',data,at)[0]
def H(data,at):return struct.unpack_from('<H',data,at)[0]
def w(data,at):return struct.unpack_from('<i',data,at)[0]
def make(blocks):buf=[C.create_string_buffer(v) for v in blocks];return buf,(Block*len(buf))(*[Block(C.cast(v,P),len(blocks[i])) for i,v in enumerate(buf)])
def get(g,k):p=P();n=S();assert buffer(g,k,C.byref(p),C.byref(n));return C.string_at(p,n.value)
def reference(kind,blocks):
 if kind==1:
  config=struct.unpack('<8I',blocks[6]);n=config[0];shift=H(blocks[3],36);height=H(blocks[3],38);points=[];uv=[]
  for i in range(n):v=blocks[0][i*68:];o=blocks[1][i*32:];points.append([w(v,0)+h(o,0),h(v,56)+h(o,6)+h(blocks[2],6),w(v,4)+h(o,2)]);uv.append([w(v,32)/16384+w(blocks[6],24)/(256*(1<<shift)),w(v,36)/16384+w(blocks[6],28)/(256*height)])
  return np.array(points,dtype=float),np.array(uv,dtype=float)
 v,o,animation=blocks[:3];height=H(blocks[4],38);width=1<<H(blocks[4],36);flags=struct.unpack_from('<I',blocks[11],256)[0];x=w(v,0)+h(o,0);z=w(v,4)+h(o,2);nx=w(v,68)+h(o,32);nz=w(v,72)+h(o,34);points=np.array([[x,h(v,8)+h(o,8),z],[nx,h(v,12)+h(o,8),nz],[nx,h(v,14)+h(o,10),nz],[x,h(v,10)+h(o,10),z]],dtype=float)
 start=H(v,40)/width+h(animation,4)/(256*width);end=start+H(v,64)/256
 if flags&2:start,end=end,start
 top=(w(v,16)+h(animation,6)//2)/(128*height);span=(w(v,24)+h(animation,6)//2)/(128*height);return points,np.array([[start,top],[end,top],[end,top+span],[start,top+span]])
def rigid(points,alpha,pa=pa,pb=pb):
 qa=np.array(pa[3:]);qb=np.array(pb[3:]);qa/=np.linalg.norm(qa);qb/=np.linalg.norm(qb);dot=float(qa@qb)
 if dot<0:qb=-qb;dot=-dot
 if dot>.9995:q=(1-alpha)*qa+alpha*qb;q/=np.linalg.norm(q)
 else:angle=math.acos(min(1.,dot));q=(math.sin((1-alpha)*angle)*qa+math.sin(alpha*angle)*qb)/math.sin(angle)
 x,y,z,s=q;R=np.array([[1-2*(y*y+z*z),2*(x*y-z*s),2*(x*z+y*s)],[2*(x*y+z*s),1-2*(x*x+z*z),2*(y*z-x*s)],[2*(x*z-y*s),2*(y*z+x*s),1-2*(x*x+y*y)]])
 return (points-((1-alpha)*np.array(pa[:3])+alpha*np.array(pb[:3])))@R.T
count={1:0,2:0};uv_unsupported=0;camera_samples=ring_samples=ring_vertices=nonempty=changed=0;max_error=0.;projection_failures=[];near_intersections=0;held=None;held_world=None;negative=0;flags_seen={}
for kind,epoch,refresh,blocks in records:
 buffers,arr=make(blocks);g=decode(epoch,refresh,kind,arr,12,65536);assert g,('Source decode',kind,refresh);meta=(Q*9)();assert info(g,meta);points,uv=reference(kind,blocks);actual=np.frombuffer(get(g,0),dtype='<f8').reshape(-1,3);assert np.array_equal(actual,points);assert meta[3]==len(points);count[kind]+=1
 if kind==1:
  original=(C.c_double*96)();attrs=C.create_string_buffer(288);assert old_road(blocks[0],len(blocks[0]),blocks[1],len(blocks[1]),blocks[2],blocks[3],len(points),meta[6],original,attrs);assert np.array_equal(np.array(original[:len(points)*3]).reshape(-1,3),points);raw_attrs=get(g,2);assert raw_attrs[:24]==attrs.raw[:24] and raw_attrs[32:]==attrs.raw[32:]
 else:
  flags_seen[str(meta[6])]=flags_seen.get(str(meta[6]),0)+1;original=(C.c_double*12)();assert old_wall(blocks[0],blocks[1],blocks[3],original)
  # Existing Q14 helper must see the same recovered world points.
  m=struct.unpack('<12i',blocks[3]);expected=[]
  def wrap(v,n):return (v+2**(n-1))%2**n-2**(n-1)
  for x,y,z in points.astype(np.int64):expected.append([wrap(wrap((int(x)+m[9])*m[0]+(int(z)+m[11])*m[6],32)>>14,16),int(y)+m[10],wrap(wrap((int(x)+m[9])*m[2]+(int(z)+m[11])*m[8],32)>>14,16)])
  assert np.array_equal(np.array(original).reshape(4,3),expected)
 if meta[7]:assert np.array_equal(np.frombuffer(get(g,1),dtype='<f8').reshape(-1,2),uv)
 else:uv_unsupported+=1;assert not get(g,1)
 if refresh<=a[3]:
  geometry_digests=[]
  for alpha in [0.,.25,.5,.75,1.]:
   output=(C.c_double*96)();assert camera(g,A,CA,B,CB,alpha,output,C.sizeof(output));cam=np.array(output[:len(points)*3]).reshape(-1,3);oracle=rigid(points,alpha);error=float(np.max(np.abs(cam-oracle)));max_error=max(max_error,error);assert error<1e-8;camera_samples+=1;geometry_digests.append(hashlib.sha256(cam.tobytes()).hexdigest())
   if not meta[7]:continue
   ring=(C.c_double*(64*6))();n=U();ok=project(g,A,CA,B,CB,alpha,proj,table,len(table),ring,C.sizeof(ring),C.byref(n))
   if not ok:projection_failures.append(dict(kind=kind,refresh=refresh,alpha=alpha,depth_min=float(cam[:,2].min()),depth_max=float(cam[:,2].max())));continue
   clipped=[]
   for i,y in enumerate(cam):
    j=(i-1)%len(cam);x=cam[j];xi=x[2]>=64;yi=y[2]>=64
    if xi!=yi:near_intersections+=1;t=(64-x[2])/(y[2]-x[2]);clipped.append((x+t*(y-x),uv[j]+t*(uv[i]-uv[j])))
    if yi:clipped.append((y,uv[i]))
   assert n.value==len(clipped);actual=np.array(ring[:n.value*6]).reshape(-1,6);ring_samples+=1;ring_vertices+=n.value;nonempty+=bool(n.value)
   if n.value:
    xyz=np.array([v[0] for v in clipped]);screen=np.column_stack([projection[0]+projection[2]*xyz[:,0]/xyz[:,2],projection[1]+projection[2]*xyz[:,1]/xyz[:,2],xyz[:,2]]);assert np.allclose(actual[:,:3],screen,atol=1e-8,rtol=0);q=np.ones(n.value) if kind==1 and meta[6] else 1/xyz[:,2];assert np.allclose(actual[:,5],q,atol=1e-10,rtol=0)
    if kind==2:assert np.allclose(actual[:,3:5],np.array([v[1] for v in clipped]),atol=1e-8,rtol=0)
    else:
     other=(C.c_double*(64*5))();on=U();attrs=get(g,2);assert old_clip(table,output,len(points),attrs,len(attrs),other,C.byref(on)) and on.value==n.value;baseline_ring=np.array(other[:on.value*5]).reshape(-1,5);assert np.array_equal(actual[:,3:5],baseline_ring[:,3:5])
  changed+=sum(v not in [geometry_digests[0],geometry_digests[-1]] for v in geometry_digests[1:-1])
 if held is None and kind==1:held=g;held_world=get(g,0);held_blocks=blocks;held_refresh=refresh;held_size=meta[8]
 else:free(g)
assert count=={1:420,2:1553} and camera_samples>9000 and changed>1000 and ring_samples>1000 and near_intersections>0 and changed==camera_samples//5*3
# Inputs are independent of lifetime; invalid owner/time/alpha/capacity reject atomically.
assert get(held,0)==held_world
for alpha in [-1.,2.,float('nan')]:
 sentinel=C.create_string_buffer(b'\xa5'*768);assert not camera(held,A,CA,B,CB,alpha,sentinel,768) and sentinel.raw==b'\xa5'*768+b'\0';negative+=1
for field in [0,1,3,4]:
 bad=(Q*5)(*b);bad[field]=0 if field in [0,1] else (a[3] if field==3 else 2);sentinel=C.create_string_buffer(b'\xa5'*768);assert not camera(held,A,CA,bad,CB,.5,sentinel,768) and sentinel.raw==b'\xa5'*768+b'\0';negative+=1
sentinel=C.create_string_buffer(b'\x5a'*8);assert not camera(held,A,CA,B,CB,.5,sentinel,8) and sentinel.raw==b'\x5a'*8+b'\0';negative+=1
for alpha,table_bytes,capacity in [(-1.,len(table),3072),(.5,len(table)-4,3072),(.5,len(table),3071)]:
 sentinel=C.create_string_buffer(b'\xa5'*3072);n=U(777);assert not project(held,A,CA,B,CB,alpha,proj,table,table_bytes,sentinel,capacity,C.byref(n)) and n.value==777 and sentinel.raw==b'\xa5'*3072+b'\0';negative+=1
bad_pose=(C.c_double*7)(*pa[:3],0,0,0,0);sentinel=C.create_string_buffer(b'\xa5'*768);assert not camera(held,A,bad_pose,B,CB,.5,sentinel,768) and sentinel.raw==b'\xa5'*768+b'\0';negative+=1
# Extended wall UV is explicitly unavailable, while world geometry remains owned.
wall_record=next(v for v in records if v[0]==2 and v[2]<=a[3]);blocks=list(wall_record[3]);context=bytearray(blocks[11]);struct.pack_into('<I',context,256,struct.unpack_from('<I',context,256)[0]|128);blocks[11]=bytes(context);buffers,arr=make(blocks);unsupported=decode(a[0],wall_record[2],2,arr,12,65536);assert unsupported;meta=(Q*9)();assert info(unsupported,meta) and not meta[7]
sentinel=C.create_string_buffer(b'\xa5'*3072);n=U(777);assert not project(unsupported,A,CA,B,CB,.5,proj,table,len(table),sentinel,3072,C.byref(n)) and n.value==777 and sentinel.raw==b'\xa5'*3072+b'\0';negative+=1;free(unsupported)
buffers,arr=make(held_blocks);assert not decode(a[0],held_refresh,1,arr,12,held_size-1);g=decode(a[0],held_refresh,1,arr,12,held_size);assert g
for v in buffers:C.memset(v,0,len(v))
assert get(g,0)==held_world;free(g);free(held)
assert before=={str(p):sha(p) for p in [rom,state]}
report=dict(result='PASS_OWNED_RECIPE_GEOMETRY_AND_CAMERA_COMPONENT' if not projection_failures else 'PARTIAL_OWNED_RECIPE_PROJECTION_DOMAIN',source_geometry_records=count,uv_unsupported_records=uv_unsupported,wall_flags=flags_seen,camera_samples=camera_samples,camera_eligible_records=camera_samples//5,newer_than_older_owner_records=len(records)-camera_samples//5,near_clip_intersections=near_intersections,max_camera_error=max_error,fractional_geometry_digests_different_from_both_endpoints=changed,projected_ring_samples=ring_samples,projected_ring_vertices=ring_vertices,nonempty_projected_rings=nonempty,projection_domain_failures=projection_failures,negative_requests_untouched=negative,exact_geometry_budget_boundary=True,geometry_survives_input_overwrite=True,core_closed_before_geometry_sampling=True,original_frames=600,original_pixels_exact=True,audio_frames=samples,audio_sha256=digest.hexdigest(),original_timing_exact=True,rom_state_sha256=before,dll_sha256=sha(out/'recipe-geometry.dll'),build_report_sha256=sha(out/'geometry-build-report.json'),script_sha256=sha(Path(__file__)),camera_pair_sha256=sha(out/'camera-pair.json'),road_archive_sha256=rr['archive_sha256'],wall_archive_sha256=wr['archive_sha256'],material_visibility_order_and_scissor_integrated=False,full_scene_fractional_gpu_verified=False,live_host_integration=False,full_scene_60fps=False)
(out/'geometry-test-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='projection_domain_failures'},indent=2));print('projection_domain_failure_count',len(projection_failures))
