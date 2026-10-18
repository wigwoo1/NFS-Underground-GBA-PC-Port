"""Measure actual retained-layer contribution; does not remove it from gameplay."""
from pathlib import Path
import os,ctypes as C,json,hashlib,collections
import numpy as np
from PIL import Image
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-retention-visibility-tests';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
scene_path=base/'NFSUG-pc-scene-tests/source-scene.dll';receipt=json.loads((base/'NFSUG-pc-scene-tests/scene-build-report.json').read_text());assert receipt['dll_sha256']==sha(scene_path)
for key in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TEST_DIRECT_CAPTURE_ROM']:os.environ.pop(key,None)
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(scene_path));core=C.CDLL(str(base/'NFSUG-pc-direct-ram-core-tests/capture-host.dll'));reader=C.CDLL(str(base/'NFSUG-pc-reader-tests/source-reader.dll'))
P=C.c_void_p;S=C.c_size_t;U=C.c_uint32;Q=C.c_uint64;I=C.c_int
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
def fn(d,n,args,r=I):f=getattr(d,n);f.argtypes=args;f.restype=r;return f
op=fn(core,'nfa_core_open',[C.c_char_p],P);close=fn(core,'nfa_core_close',[P],None);load=fn(core,'nfa_core_load_state',[P,P,S]);step=fn(core,'nfa_core_step',[P,U]);pixels=fn(core,'nfa_core_pixels',[P],P);audio=fn(core,'nfa_core_read_audio',[P,P,S],S);timing=fn(core,'nfa_core_timing',[P,P]);bind=fn(reader,'nf_pc_source_api_bind_owner',[P]);rop=fn(reader,'nf_pc_source_reader_open',[P,S],P);rcap=fn(reader,'nf_pc_source_reader_capture',[P,S],P);rclose=fn(reader,'nf_pc_source_reader_close',[P],None);frame_info=fn(reader,'nf_pc_source_frame_info',[P,P]);frame_free=fn(reader,'nf_pc_source_frame_free',[P],None)
prepare=fn(d,'nf_pc_scene_prepare',[P,S],P);scene_free=fn(d,'nf_pc_scene_free',[P],None);ret_info=fn(d,'nf_pc_scene_retention_info',[P,U,U,P]);ret_buffer=fn(d,'nf_pc_scene_retention_buffer',[P,U,U,U,P,P]);gpu_open=fn(d,'nf_pc_scene_gpu_open',[],P);gpu_close=fn(d,'nf_pc_scene_gpu_close',[P],None);gpu_error=fn(d,'nf_pc_scene_gpu_error',[],C.c_char_p);gpu_renderer=fn(d,'nf_pc_scene_gpu_renderer',[P],C.c_char_p);draw=fn(d,'nf_pc_scene_gpu_draw_passes',[P,P,U,U,U,U,U,P,S])
targets={int(p.stem) for p in (base/'NFSUG-pc-scene-tests/references').glob('*.scene')};assert len(targets)==9;rows=[]
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';before={str(p):sha(p) for p in [rom,state]};data=state.read_bytes();h=op(os.fsencode(rom));assert h and load(h,data,len(data));pcm=(C.c_int16*8192)();digest=hashlib.sha256();samples=0
for name in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn(core,'nfa_core_'+name,[P,I])(h,1)
api=API(C.sizeof(API),h,*[C.cast(getattr(core,'nfa_core_'+name),P).value for name in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert bind(C.byref(api));r=rop(C.byref(api),64*1024*1024);assert r;initial=(Q*4)();assert timing(h,initial);g=gpu_open();assert g,gpu_error();renderer=gpu_renderer(g).decode()
def render(scene,width,height,aw,ah,passes):
 raw=C.create_string_buffer(width*height*4);assert draw(g,scene,width,height,aw,ah,passes,raw,len(raw)),gpu_error();return np.frombuffer(raw.raw,dtype=np.uint8).reshape(height,width,4)[::-1].copy()
try:
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for index in range(600):
   assert step(h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1;assert C.string_at(pixels(h),153600)==oracle.read(153600);tick=(Q*4)();assert timing(h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==initial[2]+index+1 and tick[3]==index+1
   while True:
    n=audio(h,pcm,4096)
    if not n:break
    samples+=n;digest.update(C.string_at(pcm,n*4))
   if tick[2] not in targets and index!=599:continue
   frame=rcap(r,64*1024*1024);assert frame;fi=(Q*8)();assert frame_info(frame,fi);scene=prepare(frame,64*1024*1024);assert scene;frame_free(frame)
   try:
    kind_map=np.zeros(38400,dtype=np.uint8);age_map=np.zeros(38400,dtype=np.uint32);old_map=np.zeros(38400,dtype=bool);retained=collections.Counter();ages=collections.Counter()
    for owner in range(fi[4]):
     for kind in [2,3]:
      ri=(Q*10)();assert ret_info(scene,owner,kind,ri);p=P();n=S();assert ret_buffer(scene,owner,kind,1,C.byref(p),C.byref(n));records=np.frombuffer(C.string_at(p,n.value),dtype='<u4').reshape(-1,4);cells=records[:,0];assert not np.any(kind_map[cells]);kind_map[cells]=kind;age_map[cells]=ri[3]-records[:,3];old_map[cells]=records[:,3]<ri[2];retained[str(kind)]+=len(cells)
    full=render(scene,240,160,240,160,15);without=render(scene,240,160,240,160,13);different=np.any(full!=without,axis=2).reshape(-1);assert not np.any(different & (kind_map==0)),('Difference outside retained ownership',fi[1]);changed_cells=np.flatnonzero(different)
    for age in age_map[changed_cells]:ages[str(int(age))]+=1
    visible_by_kind={str(k):int(np.count_nonzero(different & (kind_map==k))) for k in [2,3]};historical_by_kind={str(k):int(np.count_nonzero(different & old_map & (kind_map==k))) for k in [2,3]}
    fourk=render(scene,3840,2160,3240,2160,15);without4k=render(scene,3840,2160,3240,2160,13);mask=np.any(fourk!=without4k,axis=2);changed_pixels=int(np.count_nonzero(mask));assert changed_pixels>0
    if index==599:
     Image.fromarray(fourk).save(out/'full-endpoint-4k.png');assert sha(out/'full-endpoint-4k.png')=='684d891677b6d97bd972aa0079fcd9495118f49c73bcdeb139f8412aab46bff2';Image.fromarray(without4k).save(out/'diagnostic-retention-omitted-4k.png');overlay=fourk.copy();overlay[mask,:3]=[255,80,0];overlay[mask,3]=255;Image.fromarray(overlay).save(out/'diagnostic-retained-contribution-4k.png')
    rows.append(dict(refresh=fi[1],owners=fi[4],source_retained_cells=dict(retained),native_resolution_different_cells=len(changed_cells),visible_by_kind=visible_by_kind,visible_writes_before_owner_begin=historical_by_kind,visible_age_histogram=dict(ages),visible_max_age_original_refreshes=max(age_map[changed_cells],default=0).item() if len(changed_cells) else 0,four_k_different_pixels=changed_pixels))
    after=(Q*4)();assert timing(h,after) and tuple(after)==tuple(tick)
   finally:scene_free(scene)
finally:gpu_close(g);rclose(r);close(h)
assert len(rows)==10 and samples==443007 and digest.hexdigest()=='eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e';assert before=={str(p):sha(p) for p in [rom,state]}
report=dict(result='PASS_RETAINED_LAYER_VISIBLE_CONTRIBUTION_AUDIT',renderer=renderer,source_frames=len(rows),original_frames=600,original_pixels_exact=True,audio_frames=samples,audio_sha256=digest.hexdigest(),four_k_changed_pixels=sum(row['four_k_different_pixels'] for row in rows),native_changed_cells=sum(row['native_resolution_different_cells'] for row in rows),historical_visible_cells=sum(sum(row['visible_writes_before_owner_begin'].values()) for row in rows),no_differences_outside_retained_cell_ownership=True,no_extra_logic_steps=True,rom_state_sha256=before,scene_dll_sha256=sha(scene_path),core_sha256=sha(base/'NFSUG-pc-direct-ram-core-tests/capture-host.dll'),test_source_sha256=sha(Path(__file__)),images_sha256={p.name:sha(p) for p in out.glob('*.png')},rows=rows,live_integration=False,full_scene_60fps=False,scope='A/B omission is a diagnostic only. Differences measure visible color/alpha influence, not all uncovered retained writes; equal colors can hide influence.')
(out/'retention-visibility-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
