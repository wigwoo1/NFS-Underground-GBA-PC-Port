from pathlib import Path
import ctypes as C,os,struct,io,json,hashlib
source=Path(__file__).parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-hud-tests';native=base/'NFSUG-android-background-jni-native-local'
with os.add_dll_directory('C:/msys64/mingw64/bin'):dll=C.CDLL(str(out/'source-hud.dll'));core=C.CDLL(str(native/'capture-host.dll'))
P=C.c_void_p;S=C.c_size_t;U=C.c_uint;Q=C.c_uint64;I=C.c_int
def fn(d,n,args,r=I):f=getattr(d,n);f.argtypes=args;f.restype=r;return f
row=fn(dll,'nf_pc_hud_row',[P,S,U,P,P,P]);decode=fn(dll,'nf_pc_hud_decode_layers',[P,S,Q,Q,S],P);prepare=fn(dll,'nf_pc_source_hud',[P,S],P);free=fn(dll,'nf_pc_hud_free',[P],None);info=fn(dll,'nf_pc_hud_info',[P,P]);buffer=fn(dll,'nf_pc_hud_buffer',[P,U,C.POINTER(P),C.POINTER(S)])
candidates=fn(dll,'nf_obj_window_scanline_prepared',[P,S,P,S,P,S,C.c_uint16,U,P,U,U,P,P,P,P])
def sha(b):return hashlib.sha256(b).hexdigest()
def blob(h,kind):p=P();n=S();assert buffer(h,kind,C.byref(p),C.byref(n));return C.string_at(p,n.value)
def check(h,g,epoch=None):
 m=(Q*5)();assert h and info(h,m);assert tuple(m[:4])==(g['epoch'] if epoch is None else epoch,g['refresh'],160,g['cells']);assert m[4]==310440
 for k in range(3):assert blob(h,k)==g['planes'][k],('HUD plane mismatch',g['name'],k)
 return m[4]
# Existing independent original-C/Java candidate corpus; rerun both freshly.
stream=io.BytesIO((base/'NFSUG-android-hud-candidates-local/hud-candidates-cases.bin').read_bytes())
def integer():return struct.unpack('>i',stream.read(4))[0]
assert integer()==0x3143484e;banks=integer();count=integer();bank=[(stream.read(98304),stream.read(1024)) for _ in range(banks)];accepted=rejected=0
for ci in range(count):
 bi,display,y,blend,brightness=[integer() for _ in range(5)];windows=(C.c_uint16*6)(*[integer() for _ in range(6)]);oam=stream.read(1024);expected=integer();gold_colors=[integer()&0xffffffff for _ in range(240 if expected else 0)];gold_tags=[integer()&0xffffffff for _ in range(240 if expected else 0)];visible=stream.read(240 if expected else 0);backdrop=stream.read(240 if expected else 0);colors=(U*240)(*[77]*240);tags=(U*240)(*[77]*240);v=(C.c_ubyte*240)(*[77]*240);b=(C.c_ubyte*240)(*[77]*240);vr,pal=bank[bi];ok=candidates(vr,len(vr),pal,len(pal),oam,len(oam),display,y,windows,blend,brightness,colors,tags,v,b);assert bool(ok)==bool(expected),('Candidate acceptance',ci)
 if ok:assert list(colors)==gold_colors and list(tags)==gold_tags and bytes(v)==visible and bytes(b)==backdrop;accepted+=1
 else:assert list(colors)==[77]*240 and list(tags)==[77]*240 and bytes(v)==bytes([77]*240) and bytes(b)==bytes([77]*240);rejected+=1
assert not stream.read() and count==1881 and accepted==1865 and rejected==16
references={};held=[];malformed=0;row_calls=0
def historical_row(layers,y):
 result=bytearray(layers[32+y*128:32+(y+1)*128])
 for part in range(25):ref=struct.unpack_from('<H',layers,20512+(y*25+part)*2)[0];result.extend(layers[28512+ref*4096:28512+ref*4096+(2048 if part==24 else 4096)])
 assert len(result)==100480;return bytes(result)
for path in sorted((out/'references').glob('*.hud')):
 raw=path.read_bytes();epoch,refresh,cells=struct.unpack('>3Q',raw[:24]);g=dict(name=path.stem,epoch=epoch,refresh=refresh,cells=cells,planes=[raw[24:153624],raw[153624:307224],raw[307224:]]);assert len(g['planes'][2])==3200;references[path.stem]=g;layers=path.with_suffix('.nlp').read_bytes();owned=C.create_string_buffer(layers);h=decode(owned,len(layers),epoch,refresh,64*1024*1024);budget=check(h,g);C.memset(owned,0,len(layers));check(h,g);held.append((h,g))
 assert not decode(layers,len(layers),epoch,refresh,budget-1);exact=decode(layers,len(layers),epoch,refresh,budget);assert exact;free(exact)
 for y in range(160):
  c=(U*240)();m=(U*240)();p=(U*5)();data=historical_row(layers,y);assert row(data,len(data),y,c,m,p);assert bytes(c)==g['planes'][0][y*960:(y+1)*960] and bytes(m)==g['planes'][1][y*960:(y+1)*960] and bytes(p)==g['planes'][2][y*20:(y+1)*20];row_calls+=1
 if len(held)==1:
  for offset,value in [(0,0),(4,2),(8,len(layers)-1),(12,159),(16,4001),(20,24),(24,2048),(28,refresh+1),(32,refresh+1),(36,1),(36+159*128,0)]:
   bad=bytearray(layers);struct.pack_into('<I',bad,offset,value);assert not decode(bytes(bad),len(bad),epoch,refresh,64*1024*1024);malformed+=1
  for offset in [20512,20512+(159*25+24)*2]:
   bad=bytearray(layers);struct.pack_into('<H',bad,offset,struct.unpack_from('<I',layers,16)[0]);assert not decode(bytes(bad),len(bad),epoch,refresh,64*1024*1024);malformed+=1
  for display in [3,0x8084,0x0084]:
   bad=bytearray(layers);struct.pack_into('<H',bad,40,display);assert not decode(bytes(bad),len(bad),epoch,refresh,64*1024*1024);malformed+=1
  data=historical_row(layers,0)
  invalid=[(data,len(data)-1,0),(data,len(data),1),(data,len(data),160),(None,len(data),0)]
  for display in [3,0x8084,0x0084]:
   bad=bytearray(data);struct.pack_into('<H',bad,8,display);invalid.append((bytes(bad),len(bad),0))
  # Unsupported final OBJ fails after earlier valid sprites, atomically.
  bad=bytearray(data);struct.pack_into('<H',bad,8,0x1404);oam_at=128+98304+1024
  for i in range(128):struct.pack_into('<4H',bad,oam_at+i*8,0x200,0,512,0)
  struct.pack_into('<H',bad,oam_at+127*8,3<<10);invalid.append((bytes(bad),len(bad),0))
  for data,n,y in invalid:
   c=(U*240)(*[77]*240);m=(U*240)(*[77]*240);p=(U*5)(*[77]*5);assert not row(data,n,y,c,m,p) and list(c)==[77]*240 and list(m)==[77]*240 and list(p)==[77]*5;malformed+=1
 assert not decode(layers,len(layers),0,refresh,64*1024*1024) and not decode(layers,len(layers),epoch,refresh+1,64*1024*1024) and not decode(layers,len(layers),epoch,refresh,64*1024*1024+1)
 sentinel=(Q*5)(*[77]*5);assert not info(None,sentinel) and list(sentinel)==[77]*5;ptr=P(123);n=S(456);assert not buffer(h,3,C.byref(ptr),C.byref(n)) and ptr.value==123 and n.value==456
assert len(references)==12 and row_calls==1920
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
bind=fn(dll,'nf_pc_source_api_bind_owner',[P]);capture=fn(dll,'nf_pc_source_frame_capture',[P,S],P);release_frame=fn(dll,'nf_pc_source_frame_free',[P],None);frame_info=fn(dll,'nf_pc_source_frame_info',[P,P]);op=fn(core,'nfa_core_open',[C.c_char_p],P);close=fn(core,'nfa_core_close',[P],None);load=fn(core,'nfa_core_load_state',[P,P,S]);step=fn(core,'nfa_core_step',[P,U]);pixels=fn(core,'nfa_core_pixels',[P],P);timing=fn(core,'nfa_core_timing',[P,P]);audio=fn(core,'nfa_core_read_audio',[P,P,S],S);layer=fn(core,'nfa_core_capture_layer_info',[P,P])
for name in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS']:os.environ.pop(name,None)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=(root/'work/integration-0.state').read_bytes();assert sha(rom.read_bytes())=='53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593' and sha(state)=='49e85564032a383626709b183f37aff34601c6e97cabdfcb17c117f72d996104'
h=op(os.fsencode(rom));assert h;api=API(C.sizeof(API),h,*[C.cast(getattr(core,'nfa_core_'+n),P).value for n in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert bind(C.byref(api));seen=set();live=[];pcm=(C.c_int16*8192)()
try:
 assert load(h,state,len(state))
 for name in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn(core,'nfa_core_'+name,[P,I])(h,1)
 initial=(Q*4)();assert timing(h,initial)
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for index in range(600):
   assert step(h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1;assert C.string_at(pixels(h),153600)==oracle.read(153600)
   while audio(h,pcm,4096):pass
   tick=(Q*4)();assert timing(h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==initial[2]+index+1 and tick[3]==index+1;display=(Q*5)()
   if not layer(h,display) or str(display[1]) not in references or display[1] in seen:continue
   refresh=display[1];frame=capture(C.byref(api),64*1024*1024);assert frame;fm=(Q*8)();assert frame_info(frame,fm);hud=prepare(frame,64*1024*1024);g=references[str(refresh)];check(hud,g,fm[0]);assert not prepare(None,64*1024*1024) and not prepare(frame,budget-1);release_frame(frame);live.append((hud,g,fm[0]));after=(Q*4)();assert timing(h,after) and tuple(after)==tuple(tick);seen.add(refresh)
   if len(seen)==9:break
 assert load(h,state,len(state)) and not capture(C.byref(api),64*1024*1024)
finally:close(h)
assert len(live)==9 and index+1==296
for hud,g,e in live:check(hud,g,e);free(hud)
for hud,g in held:check(hud,g);free(hud)
r=dict(result='PASS_PC_SOURCE_HUD',frames=12,rows=1920,direct_row_calls=row_calls,candidate_cases=count,candidate_accepted=accepted,candidate_rejected=rejected,exact_plane_bytes=12*307200,exact_parameter_words=12*800,all_planes_parameters_exact=True,malformed_layer_row_cases=malformed,atomic_failure_and_output_guards=True,mutable_input_overwritten=True,exact_and_short_budget_verified=True,maximum_retained_bytes=budget,live_frames=9,original_prefix_frames=index+1,clock_hz=16777216,cycles_per_step=280896,original_pixels_exact=True,decode_never_steps_logic=True,state_reload_rejects_stale_capture=True,owned_after_core_close=True,dll_sha256=sha((out/'source-hud.dll').read_bytes()),core_sha256=sha((native/'capture-host.dll').read_bytes()),gpu_submitted=False,playable_native_release=False,full_scene_60fps=False)
(out/'hud-report.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
