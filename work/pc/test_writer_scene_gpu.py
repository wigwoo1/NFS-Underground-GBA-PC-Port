from pathlib import Path
import os,ctypes as C,json,hashlib,struct,zlib
import numpy as np
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-writer-scene-tests'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint;I=C.c_int
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
def fn(lib,name,args,res=I):f=getattr(lib,name);f.argtypes=args;f.restype=res;return f
def blob(f,*args):p=P();n=S();assert f(*args,C.byref(p),C.byref(n));return C.string_at(p,n.value)
def part(b,i):at,n=struct.unpack_from('<2Q',b,64+i*16);assert at+n<=len(b);return b[at:at+n]
receipt=json.loads((out/'recipe-gpu-build-report.json').read_text());assert sha(out/'recipe-gpu.dll')==receipt['dll_sha256']
for p,h in receipt['source_sha256'].items():assert sha(p)==h,p
with os.add_dll_directory('C:/msys64/mingw64/bin'):
 d=C.CDLL(str(out/'recipe-gpu.dll'));core=C.CDLL(str(base/'NFSUG-pc-recipe-runtime-tests/capture-host.dll'));reader=C.CDLL(str(base/'NFSUG-pc-reader-tests/source-reader.dll'))
co=fn(core,'nfa_core_open',[C.c_char_p],P);cl=fn(core,'nfa_core_close',[P],None);load=fn(core,'nfa_core_load_state',[P,P,S]);step=fn(core,'nfa_core_step',[P,U]);audio=fn(core,'nfa_core_read_audio',[P,P,S],S);timing=fn(core,'nfa_core_timing',[P,P]);pixels=fn(core,'nfa_core_pixels',[P],P)
bind=fn(reader,'nf_pc_source_api_bind_owner',[P]);ro=fn(reader,'nf_pc_source_reader_open',[P,S],P);capture=fn(reader,'nf_pc_source_reader_capture',[P,S],P);rf=fn(reader,'nf_pc_source_frame_free',[P],None);rr=fn(reader,'nf_pc_source_reader_close',[P],None);fi=fn(reader,'nf_pc_source_frame_info',[P,P]);oi=fn(reader,'nf_pc_source_frame_owner',[P,U,P]);component=fn(reader,'nf_pc_source_frame_component',[P,U,U,P,P]);prepare=fn(d,'nf_pc_scene_prepare',[P,S],P);sf=fn(d,'nf_pc_scene_free',[P],None);sb=fn(d,'nf_pc_scene_buffer',[P,U,P,P]);scene_draw=fn(d,'nf_pc_scene_gpu_render_scene_writer',[P,P,U,P,U,P,P,P,U,U,U])
project=here.parent.parent;rom=project.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=project/'work/integration-0.state';unchanged={str(p):sha(p) for p in [rom,state]};saved=state.read_bytes();h=co(os.fsencode(rom));assert h and load(h,saved,len(saved))
for name in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn(core,'nfa_core_'+name,[P,I])(h,1)
api=API(C.sizeof(API),h,*[C.cast(getattr(core,'nfa_core_'+name),P).value for name in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert bind(C.byref(api));rh=ro(C.byref(api),64*1024*1024);assert rh
pcm=(C.c_int16*8192)();digest=hashlib.sha256();samples=0;initial=(Q*4)();assert timing(h,initial);scenes=[];real={};captured=[];scene_keys={}
try:
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for index in range(600):
   assert step(h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1;assert C.string_at(pixels(h),153600)==oracle.read(153600)
   tick=(Q*4)();assert timing(h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==initial[2]+index+1 and tick[3]==index+1
   while True:
    n=audio(h,pcm,4096)
    if not n:break
    samples+=n;digest.update(C.string_at(pcm,n*4))
   if tick[2] not in range(12434,12440):continue
   f=capture(rh,64*1024*1024);assert f
   try:
    meta=(Q*8)();assert fi(f,meta);scene=prepare(f,64*1024*1024);assert scene;scenes.append(scene)
    layers=part(part(part(blob(component,f,0,0),0),0),2);pal=np.empty((160,256,4),np.uint8)
    for y in range(160):
     page=struct.unpack_from('<H',layers,20512+(y*25+24)*2)[0];colors=np.frombuffer(layers,'<u2',256,28512+page*4096)
     for c in range(3):v=(colors>>(c*5))&31;pal[y,:,c]=(v<<3)|(v>>2)
     pal[y,:,3]=255
    assert blob(sb,scene,1)==pal.tobytes();captured.append(dict(refresh=int(meta[1]),owners=int(meta[4]),split_row=int(meta[3]),palette_sha256=hashlib.sha256(pal.tobytes()).hexdigest(),distinct_palette_rows=len(np.unique(pal.reshape(160,-1),axis=0))))
    for owner in range(meta[4]):
     key=(Q*5)();assert oi(f,owner,key);top=int(meta[3]) if owner else 0;bottom=160 if meta[4]==1 or owner else int(meta[3]);real[(tuple(key),top,bottom)]=(scene,owner,pal.copy());scene_keys[(scene,owner)]=tuple(key)
   finally:rf(f)
finally:rr(rh);cl(h)
assert samples==443007 and digest.hexdigest()=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e'
print('REAL_SCENE_PALETTES_CAPTURED_CORE_CLOSED',captured,flush=True)
original=here/'test_writer_gpu.py';text=original.read_text().replace('NFSUG-pc-writer-gpu-tests','NFSUG-pc-writer-scene-tests')
start=text.index('y,index=np.indices');end=text.index('try:\n for name,h in cr[',start)
text=text[:start]+"rows=[];compared=uncertain_total=boundary_differences=endpoint_pixels=map_bytes=reference_cells=bindings=0;images={}\n"+text[end:]
anchor='kind,top,bottom,hn=fields[5:];c=geo';assert text.count(anchor)==1
text=text.replace(anchor,"kind,top,bottom,hn=fields[5:];selection=next((k for k in real if k==(tuple(key),top,bottom)),None) or next(k for k in real if k[0]==tuple(key));top,bottom=selection[1:];c=geo")
anchor='  owner_alpha=0. if list(key)==a else 1.';assert text.count(anchor)==1;text=text.replace(anchor,"  active_scene,active_owner,palette=real[selection];pb=palette.tobytes()\n"+anchor)
text=text.replace('for index_mode in [1,0]:','for index_mode in [0]:')
anchor="mesh=env['mesh'];mf=env['mf'];ring=geo['ring'];";assert text.count(anchor)==1;text=text.replace(anchor,anchor+'draw=bound_draw;')
text=text.replace("'PASS_RAW_WRITER_TEXTURES_IN_PROJECTIVE_GPU_MASKS'","'PASS_REAL_SCENE_PALETTE_WRITER_GPU'")
text=text.replace("out/'writer-gpu-test-report.json'","out/'writer-scene-gpu-test-report.json'")
text=text.replace('-writer-textures-4k.png','-real-palette-writer-textures-4k.png').replace('Exact endpoint indices plus synthetic row-palette colors.','Exact endpoint colors using independently decoded historical display-row palettes, intersected with actual owner bands.')
env={ '__file__':str(original),'__name__':'writer_real_palette_test','real':real};guarded=0
# No borrowed frame/core data survives into these draws. Use the owned scene.
def bound_draw(g,ring,n,bounds,w,m,palette,pbytes,aw,ah,endpoint,index_mode):
 global guarded
 assert index_mode==0 and palette==env['pb'] and pbytes==163840
 s,owner=env['active_scene'],env['active_owner']
 if not guarded:
  read=env['geo']['read'];before=C.create_string_buffer(aw*ah*4);after=C.create_string_buffer(len(before));assert read(g,before,len(before))
  assert not scene_draw(g,None,owner,ring,n,bounds,w,m,aw,ah,endpoint)
  assert not scene_draw(g,s,99,ring,n,bounds,w,m,aw,ah,endpoint)
  assert not scene_draw(g,s,owner,ring,n,(U*4)(bounds[0],bounds[1],160,161),w,m,aw,ah,endpoint)
  other,other_owner=next((scene,slot) for (scene,slot),key in scene_keys.items() if key!=tuple(env['key']));assert not scene_draw(g,other,99,ring,n,bounds,w,m,aw,ah,endpoint)
  # Exact owner mismatch using a valid owner slot from a different scene.
  assert not scene_draw(g,other,other_owner,ring,n,bounds,w,m,aw,ah,endpoint)
  assert read(g,after,len(after)) and before.raw==after.raw;guarded=5
 return scene_draw(g,s,owner,ring,n,bounds,w,m,aw,ah,endpoint)
env['bound_draw']=bound_draw
try:exec(compile(text,str(original),'exec'),env)
finally:
 for scene in scenes:sf(scene)
for p,h in unchanged.items():assert sha(Path(p))==h
r=dict(coverage_policy='Original fixture coverage intersected with the actual selected display scene owner band; no widening of scene bounds or owner guard',result='PASS_OWNED_HISTORICAL_PALETTE_WRITER_BINDING',captured=captured,negative_scene_owner_band_requests=guarded,scene_survives_frame_reader_core_close=True,original_frames_exact=600,audio_frames=samples,audio_sha256=digest.hexdigest(),original_timing_exact=True,rom_state_unchanged=unchanged,gpu_dll_sha256=sha(out/'recipe-gpu.dll'),core_sha256=sha(base/'NFSUG-pc-recipe-runtime-tests/capture-host.dll'),source_test_sha256=sha(original),executed_test_sha256=hashlib.sha256(text.encode()).hexdigest(),script_sha256=sha(Path(__file__)),full_scene_60fps=False,live_integration=False,scope='Real historical scene palettes and exact scene-owner binding; endpoint and fractional isolated retained-layer colors, not interleaved full-scene composition or destination owner-band clipping.')
(out/'writer-scene-palette-report.json').write_text(json.dumps(r,indent=2));print(r['result'])
