from pathlib import Path
import ctypes as C,os,struct,io,json,hashlib,threading
import numpy as np
from PIL import Image
from gles_scene_reference import GLESSceneReference
source=Path(__file__).parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-scene-tests';refs=out/'references';native=base/'NFSUG-android-background-jni-native-local'
with os.add_dll_directory('C:/msys64/mingw64/bin'):dll=C.CDLL(str(out/'source-scene.dll'));core=C.CDLL(str(native/'capture-host.dll'))
P=C.c_void_p;S=C.c_size_t;U=C.c_uint;Q=C.c_uint64;I=C.c_int
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
def fn(d,n,args,r=I):f=getattr(d,n);f.argtypes=args;f.restype=r;return f
hud_info=fn(dll,'nf_pc_scene_hud_info',[P,P]);hud_buffer=fn(dll,'nf_pc_scene_hud_buffer',[P,U,C.POINTER(P),C.POINTER(S)])
retention_info=fn(dll,'nf_pc_scene_retention_info',[P,U,U,P]);retention_buffer=fn(dll,'nf_pc_scene_retention_buffer',[P,U,U,U,C.POINTER(P),C.POINTER(S)]);passes=fn(dll,'nf_pc_scene_gpu_draw_passes',[P,P,U,U,U,U,U,P,S])
prepare=fn(dll,'nf_pc_scene_prepare',[P,S],P);release_scene=fn(dll,'nf_pc_scene_free',[P],None);scene_info=fn(dll,'nf_pc_scene_info',[P,P]);command_info=fn(dll,'nf_pc_scene_command_info',[P,U,P]);scene_buffer=fn(dll,'nf_pc_scene_buffer',[P,U,C.POINTER(P),C.POINTER(S)]);command_buffer=fn(dll,'nf_pc_scene_command_buffer',[P,U,U,C.POINTER(P),C.POINTER(S)]);command_image=fn(dll,'nf_pc_scene_command_image',[P,U,U,C.POINTER(P),C.POINTER(S)]);command_columns=fn(dll,'nf_pc_scene_command_columns',[P,U,U,P,S])
op=fn(core,'nfa_core_open',[C.c_char_p],P);close=fn(core,'nfa_core_close',[P],None);load=fn(core,'nfa_core_load_state',[P,P,S]);step=fn(core,'nfa_core_step',[P,U]);pixels=fn(core,'nfa_core_pixels',[P],P);timing=fn(core,'nfa_core_timing',[P,P]);audio=fn(core,'nfa_core_read_audio',[P,P,S],S);layer=fn(core,'nfa_core_capture_layer_info',[P,P]);bind=fn(dll,'nf_pc_source_api_bind_owner',[P]);capture=fn(dll,'nf_pc_source_frame_capture',[P,S],P);release_frame=fn(dll,'nf_pc_source_frame_free',[P],None);frame_info=fn(dll,'nf_pc_source_frame_info',[P,P])
gpu_open=fn(dll,'nf_pc_scene_gpu_open',[],P);gpu_close=fn(dll,'nf_pc_scene_gpu_close',[P],None);gpu_error=fn(dll,'nf_pc_scene_gpu_error',[],C.c_char_p);gpu_renderer=fn(dll,'nf_pc_scene_gpu_renderer',[P],C.c_char_p);gpu_draw=fn(dll,'nf_pc_scene_gpu_draw',[P,P,U,U,U,U,P,S])
def sha(raw):return hashlib.sha256(raw).hexdigest()
def blob(f,*args):p=P();n=S();assert f(*args,C.byref(p),C.byref(n));return C.string_at(p,n.value) if n.value else b''
def reference(path):
 stream=io.BytesIO(path.read_bytes())
 def integer():return struct.unpack('>I',stream.read(4))[0]
 def buffer():return stream.read(integer())
 epoch,refresh,owners,cut,count=struct.unpack('>2Q3I',stream.read(28));background=buffer();palette=buffer();commands=[]
 for _ in range(count):
  info=struct.unpack('>16Q',stream.read(128));vertices=buffer();planes=buffer();images=[buffer() for _ in range(integer())];columns={}
  for _ in range(integer()):width=integer();columns[width]=list(struct.unpack('<'+str(width)+'I',stream.read(width*4)))
  commands.append(dict(info=info,vertices=vertices,planes=planes,images=images,columns=columns))
 assert not stream.read();return dict(epoch=epoch,refresh=refresh,owners=owners,cut=cut,background=background,palette=palette,commands=commands)
references={int(p.stem):reference(p) for p in refs.glob('*.scene')};assert len(references)==9
retentions={}
for path in (base/'NFSUG-pc-retention-tests/references').glob('*.ret'):
 data=path.read_bytes();key=tuple(map(int,path.stem.split('-')));retentions[key]=(struct.unpack('>5Q4I',data[:56]),data[56:153656],data[153656:])
for refresh,gold in references.items():
 stream=io.BytesIO((refs/f'{refresh}.edge').read_bytes())
 def integer():return struct.unpack('>I',stream.read(4))[0]
 draws=[]
 for _ in range(integer()):
  owner,kind,top,bottom=struct.unpack('>4I',stream.read(16));source_bytes=stream.read(integer());records=stream.read(integer());draws.append(dict(owner=owner,kind=kind,top=top,bottom=bottom,source=source_bytes,records=records))
 assert not stream.read();gold['retained']=draws
assert len(retentions)==34
for refresh,gold in references.items():
 raw=(base/f'NFSUG-pc-hud-tests/references/{refresh}.hud').read_bytes();epoch,tick,cells=struct.unpack('>3Q',raw[:24]);assert tick==refresh;gold['hud']=dict(epoch=epoch,refresh=tick,cells=cells,colors=raw[24:153624],metadata=raw[153624:307224],parameters=[list(struct.unpack('<5I',raw[307224+y*20:307224+(y+1)*20])) for y in range(160)],raw_parameters=raw[307224:])


models=worlds=command_count=plane_count=upload_bytes=retained_cells=0;peak=0

def check(scene,gold):
 global models,worlds,command_count,plane_count,upload_bytes,retained_cells,peak
 m=(Q*8)();assert scene_info(scene,m);assert (m[1],m[2],m[3],m[7])==(gold['refresh'],gold['owners'],len(gold['commands']),gold['cut']);peak=max(peak,m[6]);assert blob(scene_buffer,scene,0)==gold['background'] and blob(scene_buffer,scene,1)==gold['palette']
 for i,c in enumerate(gold['commands']):
  info=(Q*16)();assert command_info(scene,i,info) and tuple(info)==c['info'],('Command metadata',gold['refresh'],i,list(info),c['info']);assert blob(command_buffer,scene,i,0)==c['vertices'];assert blob(command_buffer,scene,i,1)==c['planes'];plane_count+=len(c['planes'])//44
  for level,image in enumerate(c['images']):assert blob(command_image,scene,i,level)==image;upload_bytes+=len(image)
  for width,expected in c['columns'].items():values=(C.c_uint32*width)();assert command_columns(scene,i,width,values,width*4) and list(values)==expected
  models+=info[1];worlds+=not info[1];command_count+=1

 for owner in range(gold['owners']):
  for kind in [2,3]:
   meta,rgba,records=retentions[gold['refresh'],owner,kind];ri=(Q*10)();assert retention_info(scene,owner,kind,ri);assert tuple(ri[:9])==meta and ri[9]==768080;assert blob(retention_buffer,scene,owner,kind,0)==rgba and blob(retention_buffer,scene,owner,kind,1)==records;retained_cells+=meta[8]
   records_array=np.frombuffer(records,'<u4').reshape(-1,4);v=np.empty((len(records_array),6,4),np.float32);xy=np.column_stack((records_array[:,0]%240,records_array[:,0]//240)).astype(np.float32);v[:,:,:2]=xy[:,None,:]+np.array([[0,0],[1,0],[0,1],[0,1],[1,0],[1,1]],np.float32)[None,:,:];v[:,:,2]=((xy[:,0]+np.float32(.5))/np.float32(240))[:,None];v[:,:,3]=((xy[:,1]+np.float32(.5))/np.float32(160))[:,None];assert blob(retention_buffer,scene,owner,kind,2)==v.tobytes()

 sentinel=(Q*10)(*[77]*10);assert not retention_info(scene,2,2,sentinel) and list(sentinel)==[77]*10;ptr=P(123);length=S(456);assert not retention_buffer(scene,0,4,0,C.byref(ptr),C.byref(length)) and ptr.value==123 and length.value==456
 hi=(Q*5)();assert hud_info(scene,hi) and hi[0]==m[0] and hi[1]==m[1] and hi[2]==160 and hi[3]==gold['hud']['cells'] and hi[4]==310440
 for k,name in enumerate(['colors','metadata','raw_parameters']):assert blob(hud_buffer,scene,k)==gold['hud'][name]
 return m[6]
java=root/'work/android/java/org/codex/nfsugpreview';ref=GLESSceneReference(java/'NativeSceneGpu.java',java/'NativeRgbaGpu.java',java/'NativeRoadEdgeGpu.java',java/'NativeHudGpu.java');ctx=gpu_open();assert ctx,gpu_error();renderer=gpu_renderer(ctx).decode();rows=[];isolated_rows=[];hud_isolated_rows=[];effect_contract=[];zero_contract=[];guard=False

def render(scene,gold,w,h,aw,ah):
 output=(C.c_ubyte*(w*h*4))();assert gpu_draw(ctx,scene,w,h,aw,ah,output,len(output)),gpu_error();actual=np.frombuffer(output,np.uint8).reshape(h,w,4);expected=ref.render_scene(gold,w,h,aw,ah);other=np.frombuffer(expected,np.uint8).reshape(h,w,4);diff=np.any(actual!=other,axis=2);coverage=actual[:,:,3]!=other[:,:,3];rows.append(dict(refresh=gold['refresh'],width=w,height=h,pixels=w*h,mismatched_pixels=int(diff.sum()),coverage_mismatches=int(coverage.sum()),color_mismatches=int((diff&~coverage).sum()),native_sha256=sha(output),gles_sha256=sha(expected),first=[dict(x=int(x),y=int(y),native=actual[y,x].tolist(),gles=other[y,x].tolist()) for y,x in np.argwhere(diff)[:8]]));assert not actual[:h-ah].any() and not actual[h-ah:,aw:].any();return bytes(output)
def isolate(scene,gold,w,h,aw,ah,mask=2,synthetic=False):
 # Independent retained reference uses original source textures and cell quads,
 # not the new combined source-index map. No geometric differences are masked.
 output=(C.c_ubyte*(w*h*4))();assert passes(ctx,scene,w,h,aw,ah,mask,output,len(output)),gpu_error();expected_scene=dict(gold,background=gold['background'] if mask&1 else bytes(153600),commands=[],retained=gold['retained'] if mask&2 else [],hud=gold['hud'] if mask&8 else None);expected=ref.render_scene(expected_scene,w,h,aw,ah);actual=bytes(output);diff=np.any(np.frombuffer(actual,np.uint8).reshape(-1,4)!=np.frombuffer(expected,np.uint8).reshape(-1,4),axis=1);row=dict(refresh=gold['refresh'],width=w,height=h,pixels=w*h,differences=int(diff.sum()),native_sha256=sha(actual),gles_sha256=sha(expected));(zero_contract if synthetic is True else effect_contract if synthetic=='effects' else hud_isolated_rows if mask&8 else isolated_rows).append(row);
 if diff.any():
  (out/'retained-native-diagnostic.raw').write_bytes(actual);(out/'retained-gles-diagnostic.raw').write_bytes(expected);(out/'retained-diagnostic.json').write_text(json.dumps(row,indent=2))
 assert not diff.any(),('Retained shader/cell mismatch',row)
 return actual
for name in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS']:os.environ.pop(name,None)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=(root/'work/integration-0.state').read_bytes();assert sha(rom.read_bytes())=='53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593';assert sha(state)=='49e85564032a383626709b183f37aff34601c6e97cabdfcb17c117f72d996104'
h=op(os.fsencode(rom));assert h;api=API(C.sizeof(API),h,*[C.cast(getattr(core,'nfa_core_'+n),P).value for n in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert bind(C.byref(api));seen=set();held=None;held_gold=None;held_hash=None;pcm=(C.c_int16*8192)();four_k=0
try:
 assert load(h,state,len(state))
 for n in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn(core,'nfa_core_'+n,[P,I])(h,1)
 initial=(Q*4)();assert timing(h,initial)
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for index in range(600):
   assert step(h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1;assert C.string_at(pixels(h),153600)==oracle.read(153600)
   while audio(h,pcm,4096):pass
   tick=(Q*4)();assert timing(h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==initial[2]+index+1 and tick[3]==index+1;display=(Q*5)()
   if not layer(h,display) or display[1] not in references or display[1] in seen:continue
   refresh=display[1];frame=capture(C.byref(api),64*1024*1024);assert frame;scene=prepare(frame,64*1024*1024);assert scene,('Scene preparation failed',refresh);gold=references[refresh]
   try:
    budget=check(scene,gold);source_meta=(Q*8)();prepared_meta=(Q*8)();assert frame_info(frame,source_meta) and scene_info(scene,prepared_meta) and prepared_meta[0]==source_meta[0];assert not prepare(None,64*1024*1024) and not prepare(frame,64*1024*1024+1);sentinel_meta=(Q*16)(*[77]*16);assert not command_info(scene,len(gold['commands']),sentinel_meta) and list(sentinel_meta)==[77]*16;ptr=P(123);size=S(456);assert not command_buffer(scene,0,2,C.byref(ptr),C.byref(size)) and ptr.value==123 and size.value==456;assert not command_image(scene,0,16,C.byref(ptr),C.byref(size)) and ptr.value==123 and size.value==456;assert not prepare(frame,budget-1);exact=prepare(frame,budget);assert exact;release_scene(exact)
   finally:release_frame(frame)
   image=render(scene,gold,240,160,240,160);isolate(scene,gold,240,160,240,160);isolate(scene,gold,240,160,240,160,9)
   if not seen or gold['owners']==1 or refresh==max(references) or refresh==11935:
    four=render(scene,gold,3840,2160,3240,2160);isolate(scene,gold,3840,2160,3240,2160);isolate(scene,gold,3840,2160,3240,2160,9);four_k+=1
    if not seen:Image.fromarray(np.frombuffer(four,np.uint8).reshape(2160,3840,4)[::-1].copy()).save(out/'hud-ordered-scene-4k.png')
   if not seen:
    # White-box shader fixture ONLY: temporarily replace index upload bytes,
    # preserving independently validated ownership/quads. Application callers
    # must treat exposed scene buffers as read-only. Restore before every
    # lifetime/whole-scene comparison. This does not represent captured index0.
    saved=[]
    try:
     for owner in range(gold['owners']):
      for kind in [2,3]:
       ptr=P();length=S();assert retention_buffer(scene,owner,kind,0,C.byref(ptr),C.byref(length));original=C.string_at(ptr,length.value);changed=bytearray(original);changed[0::4]=bytes(38400);saved.append((ptr,original));C.memmove(ptr,bytes(changed),len(changed))
     zero_gold=dict(gold,retained=[{k:v for k,v in dict(d,source=bytes(len(d['source']))).items() if k in ['owner','kind','top','bottom','source','records']} for d in gold['retained']])
     isolate(scene,zero_gold,240,160,240,160,3,True);isolate(scene,zero_gold,3840,2160,3240,2160,3,True)
    finally:
     for ptr,original in saved:C.memmove(ptr,original,len(original))
    restored=(C.c_ubyte*153600)();assert gpu_draw(ctx,scene,240,160,240,160,restored,len(restored)) and sha(restored)==sha(image)
   if not seen:
    # Independent synthetic historical OBJ/effects fixture, not captured game
    # provenance. Exercise all four blend modes over varied present/absent BG.
    raw=(base/'NFSUG-pc-hud-tests/references/synthetic-effects.hud').read_bytes();synthetic_hud=dict(colors=raw[24:153624],metadata=raw[153624:307224],raw_parameters=raw[307224:],parameters=[list(struct.unpack('<5I',raw[307224+y*20:307224+(y+1)*20])) for y in range(160)]);saved=[]
    yy,xx=np.indices((160,240));bg=np.empty((160,240,4),np.uint8);bg[:,:,0]=(xx*17+yy*7)%256;bg[:,:,1]=(xx*5+yy*13)%256;bg[:,:,2]=(xx*11+yy*3)%256;bg[:,:,3]=np.where(xx%8==0,0,255);background=bg.tobytes()
    try:
     ptr=P();length=S();assert scene_buffer(scene,0,C.byref(ptr),C.byref(length));saved.append((ptr,C.string_at(ptr,length.value)));C.memmove(ptr,background,len(background))
     for kind,name in enumerate(['colors','metadata','raw_parameters']):
      ptr=P();length=S();assert hud_buffer(scene,kind,C.byref(ptr),C.byref(length));saved.append((ptr,C.string_at(ptr,length.value)));C.memmove(ptr,synthetic_hud[name],length.value)
     effect_gold=dict(gold,background=background,hud=synthetic_hud)
     isolate(scene,effect_gold,240,160,240,160,9,'effects');isolate(scene,effect_gold,3840,2160,3240,2160,9,'effects')
    finally:
     for ptr,original in saved:C.memmove(ptr,original,len(original))
    restored=(C.c_ubyte*153600)();assert gpu_draw(ctx,scene,240,160,240,160,restored,len(restored)) and sha(restored)==sha(image)
   if not guard:
    sentinel=C.create_string_buffer(b'unchanged');assert not gpu_draw(ctx,scene,240,160,240,160,sentinel,8) and sentinel.raw.startswith(b'unchanged');valid=(C.c_ubyte*153600)();valid[0]=77;assert not passes(ctx,scene,240,160,240,160,16,valid,len(valid)) and valid[0]==77;wrong=[];thread=threading.Thread(target=lambda:wrong.append(gpu_draw(ctx,scene,240,160,240,160,valid,len(valid))));thread.start();thread.join();assert wrong==[0];guard=True
   after=(Q*4)();assert timing(h,after) and tuple(after)==tuple(tick),'Scene preparation/render advanced logic';seen.add(refresh)
   if held:release_scene(held)
   held=scene;held_gold=gold;held_hash=sha(image)
   if seen==set(references):break
 assert load(h,state,len(state)) and not capture(C.byref(api),64*1024*1024);assert fn(core,'nfa_core_capture_enable',[P,I])(h,0) and not capture(C.byref(api),64*1024*1024)
finally:close(h);gpu_close(ctx);ref.close()
result=[]
def recreate():
 context=gpu_open()
 try:
  assert context,gpu_error();output=(C.c_ubyte*153600)();assert gpu_draw(context,held,240,160,240,160,output,len(output)),gpu_error();assert sha(output)==held_hash;result.append(True)
 finally:
  if context:gpu_close(context)
thread=threading.Thread(target=recreate);thread.start();thread.join();release_scene(held);assert result==[True] and len(seen)==9 and four_k==4 and command_count==417 and models==29 and worlds==388
r=dict(result='PC_ORDERED_SCENE_LIVE_GPU_DIAGNOSTIC',renderer=renderer,reference_renderer=ref.renderer,source_frames=9,owners=sum(g['owners'] for g in references.values()),commands=command_count,models=models,world_surfaces=worlds,texture_planes=plane_count,compared_upload_bytes=upload_bytes,maximum_retained_scene_bytes=peak,all_prepared_commands_buffers_palettes_images_columns_exact=True,native_targets=9,four_k_targets=four_k,gpu_pixel_comparisons=sum(row['pixels'] for row in rows),gpu_pixel_differences=sum(row['mismatched_pixels'] for row in rows),original_prefix_frames=index+1,clock_hz=16777216,cycles_per_step=280896,original_pixels_exact=True,preparation_render_never_steps_logic=True,exact_and_short_budget_verified=True,source_frame_free_before_render=True,scene_survives_core_close_and_new_render_thread=True,short_output_and_wrong_thread_guards=True,metadata_buffer_guards=True,source_epoch_binding_verified=True,reload_disable_reject_stale_capture=True,dll_sha256=sha((out/'source-scene.dll').read_bytes()),core_sha256=sha((native/'capture-host.dll').read_bytes()),frames=rows,retained_road_wall_submitted=True,hud_submitted=True,hud_exact_gpu_pixels=sum(row['pixels'] for row in hud_isolated_rows),hud_gpu_differences=sum(row['differences'] for row in hud_isolated_rows),hud_targets=hud_isolated_rows,synthetic_hud_effect_targets=effect_contract,synthetic_hud_effect_pixels=sum(row['pixels'] for row in effect_contract),synthetic_hud_effect_differences=sum(row['differences'] for row in effect_contract),endpoint_layers_submitted=True,retained_cells=retained_cells,retained_zero_index_cells=sum(sum(1 for i in range(38400) if rgba[i*4]==0 and rgba[i*4+3]==255) for _,rgba,_ in retentions.values()),retained_exact_gpu_pixels=sum(row['pixels'] for row in isolated_rows),retained_gpu_differences=sum(row['differences'] for row in isolated_rows),retained_targets=isolated_rows,synthetic_zero_index_and_background_targets=zero_contract,synthetic_zero_index_pixels=sum(row['pixels'] for row in zero_contract),synthetic_uploads_restored=True,full_scene=False,playable_native_release=False,full_scene_60fps=False)
(out/'scene-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['frames','retained_targets','synthetic_zero_index_and_background_targets','hud_targets','synthetic_hud_effect_targets']},indent=2))
