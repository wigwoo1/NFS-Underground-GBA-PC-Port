from pathlib import Path
import argparse
import os,ctypes as C,json,hashlib,struct,threading,math
import numpy as np
from PIL import Image
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace')
parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=base/'NFSUG-pc-sky-gpu-tests');out=parser.parse_args().output_dir
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
receipt=json.loads((out/'sky-gpu-build-report.json').read_text());assert receipt['dll_sha256']==sha(out/'source-sky-gpu.dll')
for name,digest in receipt['extension_sha256'].items():assert sha(here/name)==digest
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'source-sky-gpu.dll'));sky=C.CDLL(str(base/'NFSUG-pc-source-sky-motion-tests/source-sky-motion.dll'))
P=C.c_void_p;S=C.c_size_t;U=C.c_uint32;Q=C.c_uint64;I=C.c_int
def fn(d,n,args,r=I):f=getattr(d,n);f.argtypes=args;f.restype=r;return f
op=fn(d,'nf_pc_scene_gpu_open',[],P);close=fn(d,'nf_pc_scene_gpu_close',[P],None);error=fn(d,'nf_pc_scene_gpu_error',[],C.c_char_p);renderer=fn(d,'nf_pc_scene_gpu_renderer',[P],C.c_char_p);draw=fn(d,'nf_pc_scene_gpu_draw_sky',[P,P,S,P,S,C.c_double,P,S,U,U,U,U,U,U,P,S]);decode=fn(sky,'nf_pc_sky_motion_decode',[P,S,P,P,S,P,S],P);sky_free=fn(sky,'nf_pc_sky_motion_free',[P],None);sample=fn(sky,'nf_pc_sky_motion_sample',[P,C.c_double,U,P,S,P,S,P,P])
g=op();assert g,error();gpu=renderer(g).decode();compared=cases=0;rows=[];covered_total=0;zero_index_pixels=0
original_roundtrip=False;original_scene_hash=None
def check(name,lo,up,weight,palette,size,band=(0,160),save=False):
 global compared,cases,covered_total,zero_index_pixels
 width,height,aw,ah=size;raw=C.create_string_buffer(width*height*4);assert draw(g,lo,15136,up,15136,weight,palette.tobytes(),163840,width,height,aw,ah,*band,raw,len(raw)),error();actual=np.frombuffer(raw.raw,dtype=np.uint8).reshape(height,width,4);expected=np.zeros((height,width,4),dtype=np.uint8)
 x=((np.arange(aw,dtype=np.int64)*2+1)*120)//aw;y=(((ah-np.arange(ah,dtype=np.int64))*2-1)*80)//ah;offset=y[:,None]*240+x[None,:]-10560;mask=(offset>=0)&(offset<15136)&(y[:,None]>=band[0])&(y[:,None]<band[1]);yy,xx=np.nonzero(mask);at=offset[mask];low=np.frombuffer(lo,dtype=np.uint8)[at];high=np.frombuffer(up,dtype=np.uint8)[at];a=palette[y[yy],low,:3].astype(np.uint32);b=palette[y[yy],high,:3].astype(np.uint32);q=int(math.floor(float(np.float32(weight))*65536+.5));colors=((a*(65536-q)+b*q+32768)//65536).astype(np.uint8);expected[yy,xx,:3]=colors;expected[yy,xx,3]=255
 differences=int(np.count_nonzero(np.any(actual!=expected,axis=2)));assert differences==0,(name,differences,int(np.max(np.abs(actual.astype(np.int16)-expected.astype(np.int16)))));compared+=width*height;cases+=1;covered_total+=len(yy);zero_index_pixels+=int(np.count_nonzero(low==0));rows.append(dict(name=name,size=size,band=band,weight=weight,q16_weight=q,covered_pixels=len(yy),pixel_differences=differences,rgba_sha256=hashlib.sha256(raw.raw).hexdigest()))
 if save:Image.fromarray(actual[::-1].copy()).save(out/'source-sky-only-4k.png')
indices=np.arange(15136,dtype=np.uint32);lo=((indices*17+5)%256).astype(np.uint8).tobytes();up=((indices*73+19)%256).astype(np.uint8).tobytes();pal=np.empty((160,256,4),dtype=np.uint8);row,index=np.indices((160,256));pal[:,:,0]=(index*37+row*11)%256;pal[:,:,1]=(index*index+row*19)%256;pal[:,:,2]=(index*13+row*row)%256;pal[:,:,3]=(index+row)%256
try:
 for size in [(240,160,240,160),(1921,1081,1621,1081),(3840,2160,3240,2160)]:
  for weight in [0.,.125,.5,.875,1.,.123456789]:check(f'synthetic-{size[0]}-{weight}',lo,up,weight,pal,size)
 for band in [(44,107),(107,108),(64,96),(0,0)]:check(f'band-{band}',lo,up,.5,pal,(3840,2160,3240,2160),band)
 fixture=base/'NFSUG-background-owner-api-fixtures/race-background-split-11878.nrb';manifest=json.loads((base/'NFSUG-background-owner-api-fixtures/background-owner-api-report.json').read_text());root=fixture.read_bytes()
 def part(b,i):at,n=struct.unpack_from('<2Q',b,64+i*16);assert at<=len(b) and n<=len(b)-at;return b[at:at+n]
 nsb=part(root,0);a,b=part(nsb,1),part(nsb,2);keys=[]
 for i in [1,2]:
  h=struct.unpack_from('<10Q',part(root,i));keys.append((Q*5)(h[3],h[4],h[5],h[6],h[8]))
 pair=decode(a,len(a),keys[0],b,len(b),keys[1],65536);assert pair
 layers=part(part(nsb,0),2);actual_pal=np.empty((160,256,4),dtype=np.uint8)
 for y in range(160):
  ref=struct.unpack_from('<H',layers,20512+(y*25+24)*2)[0];colors=np.frombuffer(layers,dtype='<u2',count=256,offset=28512+ref*4096)
  for c in range(3):v=(colors>>(c*5))&31;actual_pal[y,:,c]=(v<<3)|(v>>2)
  actual_pal[y,:,3]=255
 lower=C.create_string_buffer(15136);upper=C.create_string_buffer(15136);weight=C.c_double();dest=U()
 for mode in [0,1]:
  for alpha in [0.,.125,.5,.875,1.]:
   assert sample(pair,alpha,mode,lower,15136,upper,15136,C.byref(weight),C.byref(dest));check(f'actual-mode{mode}-alpha{alpha}',lower.raw,upper.raw,weight.value,actual_pal,(3840,2160,3240,2160),save=(mode==1 and alpha==.5))
 sky_free(pair)
 sentinel=C.create_string_buffer(b'\xa5'*153600);assert not draw(g,lo,15135,up,15136,.5,pal.tobytes(),163840,240,160,240,160,0,160,sentinel,153600) and sentinel.raw==b'\xa5'*153600+b'\0'
 tiny=C.create_string_buffer(b'\x5a'*64);assert not draw(g,lo,15136,up,15136,.5,pal.tobytes(),163840,240,160,240,160,0,160,tiny,64) and tiny.raw==b'\x5a'*64+b'\0'
 thread_result=[]
 def wrong_thread():thread_result.append(draw(g,lo,15136,up,15136,.5,pal.tobytes(),163840,240,160,240,160,0,160,sentinel,153600))
 t=threading.Thread(target=wrong_thread);t.start();t.join();assert thread_result==[0] and sentinel.raw==b'\xa5'*153600+b'\0'
 # Changing the palette between draws must replace GPU upload state completely.
 check('restored-after-actual',lo,up,.5,pal,(240,160,240,160))
 # Existing full-scene endpoint API must survive the new pass and target resizes.
 with os.add_dll_directory('C:/msys64/mingw64/bin'):
  core=C.CDLL(str(base/'NFSUG-pc-direct-ram-core-tests/capture-host.dll'));reader=C.CDLL(str(base/'NFSUG-pc-reader-tests/source-reader.dll'));baseline=C.CDLL(str(base/'NFSUG-pc-scene-tests/source-scene.dll'))
 class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
 co=fn(core,'nfa_core_open',[C.c_char_p],P);cl=fn(core,'nfa_core_close',[P],None);load=fn(core,'nfa_core_load_state',[P,P,S]);step=fn(core,'nfa_core_step',[P,U]);audio=fn(core,'nfa_core_read_audio',[P,P,S],S);bind=fn(reader,'nf_pc_source_api_bind_owner',[P]);ro=fn(reader,'nf_pc_source_reader_open',[P,S],P);rc=fn(reader,'nf_pc_source_reader_capture',[P,S],P);rf=fn(reader,'nf_pc_source_frame_free',[P],None);rr=fn(reader,'nf_pc_source_reader_close',[P],None)
 project=here.parent.parent;rom=project.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=(project/'work/integration-0.state').read_bytes();h=co(os.fsencode(rom));assert h and load(h,state,len(state));pcm=(C.c_int16*8192)()
 for name in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn(core,'nfa_core_'+name,[P,I])(h,1)
 api=API(C.sizeof(API),h,*[C.cast(getattr(core,'nfa_core_'+name),P).value for name in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert bind(C.byref(api));r=ro(C.byref(api),64*1024*1024);assert r
 for index in range(600):
  assert step(h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1
  while audio(h,pcm,4096):pass
 frame=rc(r,64*1024*1024);assert frame;prepare=fn(d,'nf_pc_scene_prepare',[P,S],P);scene=prepare(frame,64*1024*1024);old_scene=fn(baseline,'nf_pc_scene_prepare',[P,S],P)(frame,64*1024*1024);assert scene and old_scene;rf(frame);rr(r);cl(h)
 draw_scene=fn(d,'nf_pc_scene_gpu_draw',[P,P,U,U,U,U,P,S]);old_gpu=fn(baseline,'nf_pc_scene_gpu_open',[],P)();assert old_gpu;old_draw=fn(baseline,'nf_pc_scene_gpu_draw',[P,P,U,U,U,U,P,S]);first=C.create_string_buffer(3840*2160*4);second=C.create_string_buffer(len(first));expected=C.create_string_buffer(len(first))
 assert old_draw(old_gpu,old_scene,3840,2160,3240,2160,expected,len(expected));assert draw_scene(g,scene,3840,2160,3240,2160,first,len(first)) and first.raw==expected.raw
 check('sky-between-original-scenes',lo,up,.5,pal,(240,160,240,160))
 assert draw_scene(g,scene,3840,2160,3240,2160,second,len(second)) and second.raw==first.raw
 endpoint=np.frombuffer(second.raw,dtype=np.uint8).reshape(2160,3840,4)[::-1].copy();Image.fromarray(endpoint).save(out/'unchanged-native-scene-4k.png');original_scene_hash=sha(out/'unchanged-native-scene-4k.png');assert original_scene_hash=='684d891677b6d97bd972aa0079fcd9495118f49c73bcdeb139f8412aab46bff2';original_roundtrip=True
 fn(d,'nf_pc_scene_free',[P],None)(scene);fn(baseline,'nf_pc_scene_free',[P],None)(old_scene);fn(baseline,'nf_pc_scene_gpu_close',[P],None)(old_gpu)
finally:close(g)
r=dict(result='PASS_SOURCE_SKY_GPU_Q16_COLOR_REFERENCE',renderer=gpu,cases=cases,pixels_compared=compared,covered_sky_pixels=covered_total,zero_index_sky_pixels=zero_index_pixels,pixel_differences=0,exact_pixel_center_tail_and_owner_bands=True,palette_colors_blended_not_indices=True,q16_color_rounding_contract=True,invalid_buffer_and_thread_rejected=True,upload_state_restored=True,existing_full_scene_matches_baseline_before_after_sky=original_roundtrip,unchanged_full_scene_png_sha256=original_scene_hash,fixture_sha256=sha(fixture),sky_sampler_dll_sha256=sha(base/'NFSUG-pc-source-sky-motion-tests/source-sky-motion.dll'),dll_sha256=sha(out/'source-sky-gpu.dll'),build_report_sha256=sha(out/'sky-gpu-build-report.json'),test_source_sha256=sha(Path(__file__)),screenshot_sha256=sha(out/'source-sky-only-4k.png'),rows=rows,live_integration=False,full_scene_60fps=False,single_driver_only=True,scope='Standalone sky pass with readback plus unchanged endpoint-scene regression; not fractional full-scene composition or timing.')
(out/'sky-gpu-test-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='rows'},indent=2))
