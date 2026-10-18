from pathlib import Path
import os,ctypes as C,json,hashlib,struct,sys,random,math
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-source-sky-motion-tests';sys.path.insert(0,str(root/'work/camera'))
from owned_sky_boundary import SkyBoundary
from owned_sky_sampler import SkyAsset
from owned_sky_scroll import source_offset
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((out/'sky-build-report.json').read_text());assert receipt['dll_sha256']==sha(out/'source-sky-motion.dll')
for name,digest in receipt['source_sha256'].items():assert sha(here/name)==digest
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'source-sky-motion.dll'));core=C.CDLL(str(base/'NFSUG-pc-direct-ram-core-tests/capture-host.dll'));reader=C.CDLL(str(base/'NFSUG-pc-reader-tests/source-reader.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint32;I=C.c_int
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
def fn(d,n,args,r=I):f=getattr(d,n);f.argtypes=args;f.restype=r;return f
decode=fn(d,'nf_pc_sky_motion_decode',[P,S,P,P,S,P,S],P);free=fn(d,'nf_pc_sky_motion_free',[P],None);info=fn(d,'nf_pc_sky_motion_info',[P,P]);sample=fn(d,'nf_pc_sky_motion_sample',[P,C.c_double,U,P,S,P,S,P,P]);lower=C.create_string_buffer(15136);upper=C.create_string_buffer(15136);checked=0;continuous_weights=0;actual_pairs=0;held=None;previous=None;seen=set();skipped=[];max_weight_error=0.
def verify(a,ak,b,bk,actual=False):
 global checked,continuous_weights,actual_pairs,held,max_weight_error
 p=decode(a,len(a),ak,b,len(b),bk,65536)
 if not p:return False
 boundaries=[SkyBoundary.decode(v[:15192]) for v in [a,b]];asset=SkyAsset(boundaries[0].asset_origin,a[15192:]);metadata=(Q*7)();assert info(p,metadata)
 for mode in [0,1]:
  for alpha in [0.,.125,.5,.875,1.]:
   weight=C.c_double(-1);destination=U();assert sample(p,alpha,mode,lower,15136,upper,15136,C.byref(weight),C.byref(destination));expected=(asset.sample if mode==0 else asset.sample_continuous)(*boundaries,alpha);assert lower.raw==expected.lower and upper.raw==expected.upper;error=abs(weight.value-expected.weight);assert error<1e-12;max_weight_error=max(max_weight_error,error);assert destination.value==boundaries[int(alpha==1)].destination;checked+=1;continuous_weights+=int(mode==1 and weight.value>0)
 if actual:actual_pairs+=1
 if held is None:held=(p,a,ak,b,bk)
 else:free(p)
 return True
op=fn(core,'nfa_core_open',[C.c_char_p],P);close=fn(core,'nfa_core_close',[P],None);load=fn(core,'nfa_core_load_state',[P,P,S]);step=fn(core,'nfa_core_step',[P,U]);pixels=fn(core,'nfa_core_pixels',[P],P);audio=fn(core,'nfa_core_read_audio',[P,P,S],S);timing=fn(core,'nfa_core_timing',[P,P]);bind=fn(reader,'nf_pc_source_api_bind_owner',[P]);rop=fn(reader,'nf_pc_source_reader_open',[P,S],P);rcap=fn(reader,'nf_pc_source_reader_capture',[P,S],P);rclose=fn(reader,'nf_pc_source_reader_close',[P],None);frame_info=fn(reader,'nf_pc_source_frame_info',[P,P]);owner_info=fn(reader,'nf_pc_source_frame_owner',[P,U,P]);component=fn(reader,'nf_pc_source_frame_component',[P,U,U,P,P]);frame_free=fn(reader,'nf_pc_source_frame_free',[P],None)
def part(b,i):at,n=struct.unpack_from('<2Q',b,64+i*16);assert at<=len(b) and n<=len(b)-at;return b[at:at+n]
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';before={str(p):sha(p) for p in [rom,state]};data=state.read_bytes();h=op(os.fsencode(rom));assert h and load(h,data,len(data));pcm=(C.c_int16*8192)();digest=hashlib.sha256();samples=0
for name in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn(core,'nfa_core_'+name,[P,I])(h,1)
api=API(C.sizeof(API),h,*[C.cast(getattr(core,'nfa_core_'+name),P).value for name in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert bind(C.byref(api));r=rop(C.byref(api),64*1024*1024);assert r;initial=(Q*4)();assert timing(h,initial)
try:
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for index in range(600):
   assert step(h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1;assert C.string_at(pixels(h),153600)==oracle.read(153600);tick=(Q*4)();assert timing(h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==initial[2]+index+1 and tick[3]==index+1
   while True:
    n=audio(h,pcm,4096)
    if not n:break
    samples+=n;digest.update(C.string_at(pcm,n*4))
   frame=rcap(r,64*1024*1024)
   if not frame:continue
   try:
    fi=(Q*8)();assert frame_info(frame,fi);p=P();n=S();assert component(frame,0,0,C.byref(p),C.byref(n));sky_root=part(C.string_at(p,n.value),0)
    for owner in range(fi[4]):
     key=(Q*5)();assert owner_info(frame,owner,key)
     if tuple(key) in seen:continue
     seen.add(tuple(key));block=part(sky_root,owner+1);assert len(block)==30568
     if previous and previous[1][0]==key[0] and previous[1][1]<key[1] and 0<key[3]-previous[1][3]<=8:
      if not verify(previous[0],previous[1],block,key,True):skipped.append(dict(older=list(previous[1]),newer=list(key)))
     previous=(block,key)
   finally:frame_free(frame)
finally:rclose(r);close(h)
assert samples==443007 and digest.hexdigest()=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e';assert before=={str(p):sha(p) for p in [rom,state]};assert actual_pairs>20 and not skipped,(actual_pairs,skipped[:2])
# Reuse actual owned ROM asset across the complete14-bit angular domain.
p,a,ak,b,bk=held;boundary=SkyBoundary.decode(a[:15192]);asset=a[15192:];origin=boundary.asset_origin
def synthetic(angle,refresh,page):
 offset=source_offset(angle,240,0);h=struct.pack('<4sIQ8IiI',b'NFSK',1,7,refresh,angle,240,64,origin+offset,origin,0x06002940+page*0xa000,15136,0,0);return h+asset[offset:offset+15136]+asset
domain_samples=0;wrap_samples=0
for angle in range(16384):
 delta=1 if angle%2 else -1;end=(angle+delta)&16383;sa,sb=synthetic(angle,1,0),synthetic(end,2,1);ka,kb=(Q*5)(7,1,1,1,0),(Q*5)(7,2,2,2,1);q=decode(sa,len(sa),ka,sb,len(sb),kb,65536);assert q;weight=C.c_double();destination=U();assert sample(q,.5,1,lower,15136,upper,15136,C.byref(weight),C.byref(destination));phase=((angle+delta*.5)*240/4096)%240;base_phase=math.floor(phase);assert lower.raw==asset[base_phase:base_phase+15136] and upper.raw==asset[(base_phase+1)%240:(base_phase+1)%240+15136] and abs(weight.value-(phase-base_phase))<1e-12;free(q);domain_samples+=1;wrap_samples+=int(abs(end-angle)>8000)
joined=0
for angle in [0,1,63,64,4095,4096,8191,8192,12287,12288,16382,16383]:
 for delta in [-8,-1,1,8]:
  blocks=[synthetic((angle+i*delta)&16383,i+1,i%2) for i in range(3)];keys=[(Q*5)(7,i+1,i+1,i+1,i%2) for i in range(3)];qa=decode(blocks[0],30568,keys[0],blocks[1],30568,keys[1],65536);qb=decode(blocks[1],30568,keys[1],blocks[2],30568,keys[2],65536);assert qa and qb
  for mode in [0,1]:
   assert sample(qa,1.,mode,lower,15136,upper,15136,C.byref(weight),C.byref(destination));end=(lower.raw,upper.raw,weight.value,destination.value);assert sample(qb,0.,mode,lower,15136,upper,15136,C.byref(weight),C.byref(destination));assert end==(lower.raw,upper.raw,weight.value,destination.value);joined+=1
  free(qa);free(qb)
negative=0
for alpha,mode in [(-1.,0),(2.,0),(float('nan'),0),(.5,2)]:
 C.memset(lower,0xa5,15136);C.memset(upper,0x5a,15136);weight=C.c_double(123);destination=U(456);assert not sample(p,alpha,mode,lower,15136,upper,15136,C.byref(weight),C.byref(destination)) and lower.raw==b'\xa5'*15136 and upper.raw==b'\x5a'*15136 and weight.value==123 and destination.value==456;negative+=1
weight=C.c_double(123);destination=U(456);assert not sample(p,.5,1,lower,15135,upper,15136,C.byref(weight),C.byref(destination));negative+=1;assert not sample(p,.5,1,lower,15136,lower,15136,C.byref(weight),C.byref(destination));negative+=1
for offset in [0,24,32,36,40,44,48,52,56,15192]:
 bad=bytearray(b);bad[offset]^=1;bad=bytes(bad);assert not decode(a,len(a),ak,bad,len(bad),bk,65536);negative+=1
metadata=(Q*7)();assert info(p,metadata);assert not decode(a,len(a),ak,b,len(b),bk,metadata[6]-1);negative+=1;q=decode(a,len(a),ak,b,len(b),bk,metadata[6]);assert q;free(q)
ka,kb=(Q*5)(7,1,1,1,0),(Q*5)(7,2,2,2,1);sa,sb=synthetic(0,1,0),synthetic(2048,2,1);assert not decode(sa,30568,ka,sb,30568,kb,65536);negative+=1
transition=bytearray(synthetic(1,2,1))
for at in [32,36]:struct.pack_into('<I',transition,at,struct.unpack_from('<I',transition,at)[0]+256)
transition=bytes(transition);assert not decode(sa,30568,ka,transition,30568,kb,65536);negative+=1
assert sample(p,.5,1,lower,15136,upper,15136,C.byref(weight),C.byref(destination));owned=(lower.raw,upper.raw,weight.value);del a,b,previous;assert sample(p,.5,1,lower,15136,upper,15136,C.byref(weight),C.byref(destination)) and (lower.raw,upper.raw,weight.value)==owned;free(p)
report=dict(result='PASS_NATIVE_SOURCE_SKY_MOTION_COMPONENT',actual_owner_pairs=actual_pairs,actual_reference_samples=checked,continuous_nonzero_weights=continuous_weights,angle_domain_samples=domain_samples,wrap_samples=wrap_samples,pair_join_checks=joined,reference_weight_max_error=max_weight_error,all_index_spans_and_16_byte_tail_exact=True,negative_requests=negative,exact_budget_boundary_verified=True,owned_after_core_close=True,retained_bytes=metadata[6],original_frames=600,original_pixels_exact=True,audio_frames=samples,audio_sha256=digest.hexdigest(),rom_state_sha256=before,core_sha256=sha(base/'NFSUG-pc-direct-ram-core-tests/capture-host.dll'),source_reference_sha256={name:sha(root/'work/camera'/name) for name in ['owned_sky_sampler.py','owned_sky_scroll.py','owned_sky_boundary.py']},dll_sha256=sha(out/'source-sky-motion.dll'),build_report_sha256=sha(out/'sky-build-report.json'),test_source_sha256=sha(Path(__file__)),live_integration=False,full_scene_60fps=False,continuous_phase_preserves_original_endpoint_pixels=False,scope='Exact-copy and continuous source-phase modes tested independently. GPU palette/color sampling and synchronization with world/retained/HUD not yet integrated.')
(out/'sky-test-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
