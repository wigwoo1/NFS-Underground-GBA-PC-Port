from pathlib import Path
import ctypes as C,hashlib,json,os,struct,threading
import numpy as np
from PIL import Image
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-background-tests';refs=out/'references';fixtures=base/'NFSUG-background-owner-api-fixtures';native=base/'NFSUG-android-background-jni-native-local'
for name in ('NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS'):os.environ.pop(name,None)
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'source-background.dll'));core=C.CDLL(str(native/'capture-host.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint;I=C.c_int
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
def fn(d,name,args,ret=I):f=getattr(d,name);f.argtypes=args;f.restype=ret;return f
op=fn(core,'nfa_core_open',[C.c_char_p],P);close=fn(core,'nfa_core_close',[P],None);load=fn(core,'nfa_core_load_state',[P,P,S]);step=fn(core,'nfa_core_step',[P,U]);pixels=fn(core,'nfa_core_pixels',[P],P);timing=fn(core,'nfa_core_timing',[P,C.POINTER(Q)]);audio=fn(core,'nfa_core_read_audio',[P,P,S],S);info=fn(core,'nfa_core_capture_layer_info',[P,C.POINTER(Q)])
bind=fn(d,'nf_pc_source_api_bind_owner',[C.POINTER(API)]);cap=fn(d,'nf_pc_source_frame_capture',[C.POINTER(API),S],P);free=fn(d,'nf_pc_source_frame_free',[P],None)
readers={name:fn(d,'nf_pc_source_'+name+'_rgba',[P,P,S]) for name in ('background','palette','sky')}
gpu_open=fn(d,'nf_pc_background_gpu_open',[],P);gpu_close=fn(d,'nf_pc_background_gpu_close',[P],None);gpu_draw=fn(d,'nf_pc_background_gpu_draw',[P,P,U,U,U,U,P,S]);gpu_error=fn(d,'nf_pc_background_gpu_error',[],C.c_char_p);gpu_renderer=fn(d,'nf_pc_background_gpu_renderer',[P],C.c_char_p)
def sha(data):return hashlib.sha256(data).hexdigest()
def addr(name):return C.cast(getattr(core,'nfa_core_'+name),P).value
def clock():v=(Q*4)();assert timing(h,v);return tuple(v)
def rendered(context,frame,width,height,active_width,active_height,expected):
 output=(C.c_ubyte*(width*height*4))();assert gpu_draw(context,frame,width,height,active_width,active_height,output,len(output)),gpu_error().decode();actual=np.ctypeslib.as_array(output).reshape(height,width,4)
 xs=np.floor((np.arange(active_width,dtype=np.float64)+.5)*240/active_width).astype(int);ys=np.floor((active_height-np.arange(active_height,dtype=np.float64)-.5)*160/active_height).astype(int)
 colors=np.frombuffer(expected,dtype=np.uint8).reshape(160,240,4);wanted=colors[ys[:,None],xs[None,:],:];match=np.all(actual[:active_height,:active_width]==wanted,axis=2)
 if not np.all(match):
  positions=np.argwhere(~match);details=[dict(x=int(x),y=int(y),source_x=int(xs[x]),source_y=int(ys[y]),expected=wanted[y,x].tolist(),actual=actual[y,x].tolist()) for y,x in positions[:16]];(out/'pixel-mismatch.json').write_text(json.dumps(dict(width=width,height=height,mismatched_pixels=len(positions),first=details),indent=2));raise AssertionError('GPU source pixel mismatch: '+str(len(positions)))
 assert not np.any(actual[active_height:]) and not np.any(actual[:active_height,active_width:]),'Uncovered target filled';return bytes(output)
selected_kinds={}
for path in fixtures.glob('source-race-background-*.nrb'):
 with path.open('rb') as stream:header=stream.read(64)
 selected_kinds[struct.unpack_from('<Q',header,32)[0]]=struct.unpack_from('<Q',header,40)[0]
selected=set(selected_kinds);rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=(root/'work/integration-0.state').read_bytes();assert sha(rom.read_bytes())=='53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593';assert sha(state)=='49e85564032a383626709b183f37aff34601c6e97cabdfcb17c117f72d996104'
h=op(os.fsencode(rom));assert h;api=API(C.sizeof(API),h,*[addr(name) for name in ('capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership')],0);assert bind(C.byref(api));ctx=gpu_open();assert ctx,gpu_error().decode();renderer=gpu_renderer(ctx).decode();seen=set();frames=[];four_k=0;rgba_checks=palette_checks=sky_checks=0;held=None;held_expected=None;guard=False;pcm=(C.c_int16*8192)()
try:
 assert load(h,state,len(state))
 for name in ('capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable'):assert fn(core,'nfa_core_'+name,[P,I])(h,1)
 initial=clock()
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for index in range(600):
   assert step(h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1;assert C.string_at(pixels(h),153600)==oracle.read(153600);before=clock();assert before[:2]==(16777216,280896) and before[2]==initial[2]+index+1 and before[3]==index+1
   while audio(h,pcm,4096):pass
   meta=(Q*5)()
   if not info(h,meta) or meta[1] not in selected or meta[1] in seen:continue
   frame=cap(C.byref(api),64*1024*1024);assert frame;refresh=meta[1];expected={}
   try:
    for name,size in [('background',153600),('palette',163840),('sky',153600)]:
     output=(C.c_ubyte*size)();assert readers[name](frame,output,size);raw=bytes(output);gold=(refs/(str(refresh)+'.'+name+'.rgba')).read_bytes();assert raw==gold,(name,refresh);expected[name]=raw
     sentinel=C.create_string_buffer(b'unchanged');assert not readers[name](frame,sentinel,8) and sentinel.raw.startswith(b'unchanged');assert not readers[name](None,sentinel,8)
    rgba_checks+=38400;palette_checks+=40960;sky_checks+=38400
    native_image=rendered(ctx,frame,240,160,240,160,expected['background']);row=dict(refresh=refresh,native_sha256=sha(native_image))
    if not seen or refresh==max(selected) or selected_kinds[refresh]==1:
     image=rendered(ctx,frame,3840,2160,3240,2160,expected['background']);row['four_k_sha256']=sha(image);four_k+=1
     if not seen:Image.fromarray(np.frombuffer(image,dtype=np.uint8).reshape(2160,3840,4)[::-1].copy()).save(out/'initial-source-background-4k.png')
    if not guard:
     sentinel=C.create_string_buffer(b'unchanged');assert not gpu_draw(ctx,frame,240,160,240,160,sentinel,8) and sentinel.raw.startswith(b'unchanged');wrong=[];thread=threading.Thread(target=lambda:wrong.append(gpu_draw(ctx,frame,240,160,240,160,sentinel,8)));thread.start();thread.join();assert wrong==[0];guard=True
    assert clock()==before,'Decoder/GPU advanced logic';frames.append(row);seen.add(refresh)
    if held:free(held)
    held=frame;held_expected=expected['background'];frame=None
   finally:
    if frame:free(frame)
   if seen==selected:break
 assert len(seen)==9 and four_k==3 and guard
finally:gpu_close(ctx);close(h)
# Recreate GL on a DIFFERENT render thread, after the real core was closed.
error=[];last_hash=frames[-1]['native_sha256']
def recreate():
 context=gpu_open()
 try:assert context,gpu_error().decode();assert sha(rendered(context,held,240,160,240,160,held_expected))==last_hash
 except BaseException as failure:error.append(repr(failure))
 finally:
  if context:gpu_close(context)
thread=threading.Thread(target=recreate);thread.start();thread.join();assert not error,error;free(held)
result=dict(result='PASS_PC_SOURCE_BACKGROUND_GPU',source_frames=9,source_background_cells=rgba_checks,historical_palette_entries=palette_checks,source_sky_cells=sky_checks,native_gpu_frames=9,four_k_frames=3,native_gpu_pixel_comparisons=9*38400+38400,four_k_pixel_comparisons=3*3840*2160,renderer=renderer,original_prefix_frames=index+1,clock_hz=16777216,cycles_per_step=280896,readers_and_gpu_never_step_logic=True,short_output_and_thread_guards=True,context_recreated_on_render_thread_after_core_close=True,source_fidelity_java_reader=True,adapter_sha256=sha((out/'source-background.dll').read_bytes()),core_sha256=sha((native/'capture-host.dll').read_bytes()),frames=frames,scope='Actual Windows source capture and INITIAL background-only GPU pass. Car/world/road/wall/HUD composition and gameplay still incomplete.',full_scene=False,full_scene_60fps=False)
result['source_sha256']={name:sha((Path(__file__).parent/name).read_bytes()) for name in ('source_frame.c','source_frame.h','source_background.c','source_background.h','background_gpu.c','background_gpu.h')}
result['test_sha256']=sha(Path(__file__).read_bytes())
(out/'background-gpu-report.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='frames'},indent=2))
