from pathlib import Path
import ctypes as C,hashlib,json,os,struct,concurrent.futures,collections
BASE=Path('C:/NFSUG-Workspace/');ROOT=Path('C:/NFSUG-Workspace/NFSUG-Native-PC-Port')
OUT=BASE/'NFSUG-pc-scene-retention-ordinals-tests';LIMIT=64*1024*1024
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((OUT/'build-report.json').read_text());assert sha(OUT/'scene-ordinals.dll')==build['dll_sha256']
with os.add_dll_directory('C:/msys64/mingw64/bin'):
    reader=C.CDLL(str(OUT/'scene-ordinals.dll'))
    core=C.CDLL(str(BASE/'NFSUG-pc-history-source-provenance-tests/capture-host.dll'))
P,S,Q,U,I=C.c_void_p,C.c_size_t,C.c_uint64,C.c_uint,C.c_int
def fn(d,name,args,result=I):
    f=getattr(d,name);f.argtypes=args;f.restype=result;return f
class API(C.Structure):
    _fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
op=fn(core,'nfa_core_open',[C.c_char_p],P);close=fn(core,'nfa_core_close',[P],None)
load=fn(core,'nfa_core_load_state',[P,P,S]);step=fn(core,'nfa_core_step',[P,U]);audio=fn(core,'nfa_core_read_audio',[P,P,S],S)
pixels=fn(core,'nfa_core_pixels',[P],P);timing=fn(core,'nfa_core_timing',[P,P])
enable=fn(core,'nf_pc_history_provenance_enable',[I]);cells=fn(core,'nf_pc_history_owner_cells',[P,U,P,S],S)
capture=fn(reader,'nf_pc_source_frame_capture',[P,S],P);bind=fn(reader,'nf_pc_source_api_bind_owner',[P]);framefree=fn(reader,'nf_pc_source_frame_free',[P],None)
finfo=fn(reader,'nf_pc_source_frame_info',[P,P]);owner=fn(reader,'nf_pc_source_frame_owner',[P,U,P])
normal=fn(reader,'nf_pc_scene_prepare_motion',[P,S],P);owned=fn(reader,'nf_pc_scene_prepare_motion_ordinals',[P,S],P)
free=fn(reader,'nf_pc_scene_free',[P],None);info=fn(reader,'nf_pc_scene_info',[P,P])
grid=fn(reader,'nf_pc_scene_retention_ordinals',[P,U,U,P,P])
sb=fn(reader,'nf_pc_scene_buffer',[P,U,P,P]);rb=fn(reader,'nf_pc_scene_retention_buffer',[P,U,U,U,P,P]);hud=fn(reader,'nf_pc_scene_hud_buffer',[P,U,P,P])
ci=fn(reader,'nf_pc_scene_command_info',[P,U,P]);cb=fn(reader,'nf_pc_scene_command_buffer',[P,U,U,P,P]);image=fn(reader,'nf_pc_scene_command_image',[P,U,U,P,P])
gpuopen=fn(reader,'nf_pc_scene_gpu_open',[],P);gpuclose=fn(reader,'nf_pc_scene_gpu_close',[P],None)
draw=fn(reader,'nf_pc_scene_gpu_draw',[P,P,U,U,U,U,P,S])
def blob(f,*args):
    p=P();n=S();assert f(*args,C.byref(p),C.byref(n));return C.string_at(p,n.value)
def readgrid(scene,role,kind):
    p=P();n=S();assert grid(scene,role,kind,C.byref(p),C.byref(n)) and n.value==38400
    return C.string_at(p,n.value*8)
def guard(scene,role,kind):
    p=P(12345);n=S(6789);assert not grid(scene,role,kind,C.byref(p),C.byref(n)) and p.value==12345 and n.value==6789
rom=ROOT.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=ROOT/'work/integration-0.state'
protected={str(p):sha(p) for p in [rom,state]}
assert not owned(None,LIMIT) and not owned(None,1) and not owned(None,LIMIT+1)
h=op(os.fsencode(rom));data=state.read_bytes();assert h and load(h,data,len(data))
for name in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:
    assert fn(core,'nfa_core_'+name,[P,I])(h,1)
assert enable(1)
api=API(C.sizeof(API),h,*[C.cast(getattr(core,'nfa_core_'+n),P).value for n in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0)
assert bind(C.byref(api));start=(Q*4)();assert timing(h,start)
counts=collections.Counter();kept=[];budget_cases=[];pcm=(C.c_int16*8192)();pcmsha=hashlib.sha256();framesha=hashlib.sha256();pcmn=0
try:
    with (BASE/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
        for index in range(600):
            assert step(h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1
            original=C.string_at(pixels(h),153600);assert original==oracle.read(153600);framesha.update(original)
            tick=(Q*4)();assert timing(h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==start[2]+index+1 and tick[3]==index+1
            while True:
                n=audio(h,pcm,4096)
                if not n:break
                pcmn+=n;pcmsha.update(C.string_at(pcm,n*4))
            frame=capture(C.byref(api),LIMIT)
            if not frame:assert index<10;continue
            a=b=None
            try:
                fi=(Q*8)();assert finfo(frame,fi);a=normal(frame,LIMIT);b=owned(frame,LIMIT);assert a and b,index
                ia=(Q*8)();ib=(Q*8)();assert info(a,ia) and info(b,ib)
                assert list(ia[:6])+[ia[7]]==list(ib[:6])+[ib[7]] and ib[6]==ia[6]+fi[4]*2*307200
                counts['scenes']+=1;counts['split_scenes']+=fi[4]==2
                hashes={}
                for role in range(fi[4]):
                    key=(Q*5)();assert owner(frame,role,key)
                    top=fi[3] if role else 0;bottom=160 if role or fi[4]==1 else fi[3]
                    for kind in [1,2]:
                        raw=C.create_string_buffer(307264);assert cells(key,kind,raw,307264)==307264
                        assert struct.unpack_from('<8Q',raw.raw)==tuple(key)+(kind,38400,307264)
                        expected=bytearray(raw.raw[64:]);expected[:top*240*8]=bytes(top*240*8);expected[bottom*240*8:]=bytes((160-bottom)*240*8)
                        actual=readgrid(b,role,kind+1);assert actual==expected,(index,role,kind)
                        hashes[(role,kind+1)]=hashlib.sha256(actual).hexdigest();counts['owned_grids']+=1;counts['cell_slots']+=38400
                        guard(a,role,kind+1);counts['default_rejections']+=1
                        for k in [0,1,2]:assert blob(rb,a,role,kind+1,k)==blob(rb,b,role,kind+1,k);counts['retained_buffer_parity']+=1
                for k in [0,1]:assert blob(sb,a,k)==blob(sb,b,k);counts['background_palette_parity']+=1
                # Full command streams compared on selected snapshots; every frame's retained layers above are exact.
                if index==18 or (fi[4]==2 and sum(case['owners']==2 for case in budget_cases)<2):
                    for i in range(ia[3]):
                        ca=(Q*16)();cc=(Q*16)();assert ci(a,i,ca) and ci(b,i,cc) and list(ca)==list(cc)
                        for k in [0,1]:assert blob(cb,a,i,k)==blob(cb,b,i,k)
                        assert blob(image,a,i,0)==blob(image,b,i,0);counts['command_parity']+=1
                    exact=owned(frame,ib[6]);assert exact;free(exact);assert not owned(frame,ib[6]-1)
                    budget_cases.append(dict(index=index,bytes=ib[6],owners=fi[4],split=fi[3]))
                    guard(b,fi[4],2);guard(b,0,0);guard(None,0,2);counts['invalid_getter_guards']+=3
                    kept.append((a,b,hashes));a=b=None
            finally:
                free(a);free(b);framefree(frame)
            if index%100==99:print('Verified original steps',index+1,flush=True)
finally:enable(0);close(h)
assert counts['scenes']==590 and len(kept)==3 and sum(case['owners']==2 for case in budget_cases)==2
baseline=json.loads((BASE/'NFSUG-pc-pose-capture-timing-tests/baseline-route.json').read_text())
assert pcmn==443007 and pcmsha.hexdigest()==baseline['pcm_sha256'] and framesha.hexdigest()==baseline['original_frames_sha256']
gpu=gpuopen();assert gpu
try:
    left=C.create_string_buffer(3840*2160*4);right=C.create_string_buffer(len(left))
    for a,b,hashes in kept:
        # Source frames and entire emulated core have been destroyed before these reads/draws.
        with concurrent.futures.ThreadPoolExecutor(1) as executor:
            for (role,kind),digest in hashes.items():
                assert hashlib.sha256(executor.submit(readgrid,b,role,kind).result()).hexdigest()==digest;counts['post_core_thread_reads']+=1
        for width,height,aw,ah in [(3840,2160,3240,2160),(613,407,601,399)]:
            n=width*height*4
            assert draw(gpu,a,width,height,aw,ah,left,n) and draw(gpu,b,width,height,aw,ah,right,n)
            assert C.string_at(left,n)==C.string_at(right,n)
            counts['gpu_endpoint_comparisons']+=1;counts['gpu_endpoint_pixels']+=width*height
finally:
    gpuclose(gpu)
    for a,b,_ in kept:free(a);free(b)
assert protected=={str(p):sha(p) for p in [rom,state]}
report=dict(result='PASS_OWNED_SCENE_EVENT_ORDINALS',counts=dict(counts),budget_cases=budget_cases,build_sha256=sha(OUT/'build-report.json'),
    dll_sha256=build['dll_sha256'],core_sha256=sha(BASE/'NFSUG-pc-history-source-provenance-tests/capture-host.dll'),test_sha256=sha(Path(__file__)),
    pcm_frames=pcmn,pcm_sha256=pcmsha.hexdigest(),original_frames_sha256=framesha.hexdigest(),protected_sha256=protected,
    lifetime_after_source_and_core_free=True,live_scheduling=False,complete_history_root_materials=False,full_scene_60fps=False)
(OUT/'test-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
