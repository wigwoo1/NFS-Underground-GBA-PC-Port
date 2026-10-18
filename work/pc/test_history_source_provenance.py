from pathlib import Path
import ctypes as C,os,json,hashlib,struct,collections,math,zipfile
base=Path('C:/NFSUG-Workspace');root=Path('Y:/CODEX/NFSUG-Native-PC-Port');out=base/'NFSUG-pc-history-source-provenance-tests';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((out/'history-build-report.json').read_text());assert sha(out/'capture-host.dll')==build['core_sha256'];baseline_path=base/'NFSUG-pc-pose-capture-timing-tests/baseline-route.json';baseline=json.loads(baseline_path.read_text())
with os.add_dll_directory('C:/msys64/mingw64/bin'):core=C.CDLL(str(out/'capture-host.dll'));reader=C.CDLL(str(base/'NFSUG-pc-scene-sample-tests/scene-sample.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint;I=C.c_int
def fn(d,n,a,r=I):f=getattr(d,n);f.argtypes=a;f.restype=r;return f
class API(C.Structure):_fields_=[('size',S),('core',P),('info',P),('background',P),('geometry',P),('road',P),('wall',P),('proof',P),('owner_thread',Q)]
op=fn(core,'nfa_core_open',[C.c_char_p],P);close=fn(core,'nfa_core_close',[P],None);load=fn(core,'nfa_core_load_state',[P,P,S]);step=fn(core,'nfa_core_step',[P,U]);pixels=fn(core,'nfa_core_pixels',[P],P);audio=fn(core,'nfa_core_read_audio',[P,P,S],S);timing=fn(core,'nfa_core_timing',[P,P]);bind=fn(reader,'nf_pc_source_api_bind_owner',[P]);capture=fn(reader,'nf_pc_source_frame_capture',[P,S],P);free=fn(reader,'nf_pc_source_frame_free',[P],None);frame_info=fn(reader,'nf_pc_source_frame_info',[P,P]);owner=fn(reader,'nf_pc_source_frame_owner',[P,U,P]);component=fn(reader,'nf_pc_source_frame_component',[P,U,U,P,P]);enable=fn(core,'nf_pc_history_provenance_enable',[I]);read=fn(core,'nf_pc_history_provenance_read',[Q,U,Q,P,S],S);stats=fn(core,'nf_pc_history_provenance_stats',[P])
def blob(f,*args):p=P();n=S();assert f(*args,C.byref(p),C.byref(n));return C.string_at(p,n.value)
owner_cells=fn(core,'nf_pc_history_owner_cells',[P,U,P,S],S);retention=fn(reader,'nf_pc_source_retention',[P,U,U,S],P);retention_free=fn(reader,'nf_pc_retention_free',[P],None);retention_buffer=fn(reader,'nf_pc_retention_buffer',[P,U,P,P])
cell_archive=zipfile.ZipFile(out/'owner-cell-sources.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=1)
cell_rows=[]
def fnv(data):
 h=14695981039346656037
 for x in data:h=((h^x)*1099511628211)&0xffffffffffffffff
 return h
def surfaces(packet):
 at,n=struct.unpack_from('<2I',packet,48);world=packet[at:at+n];assert world[:4]==b'RFD1';count=struct.unpack_from('<I',world,4)[0];ids_at,ids_n=struct.unpack_from('<2I',packet,84);ids=packet[ids_at:ids_at+ids_n];assert ids[:4]==b'NFI1';result=collections.defaultdict(list);at=8
 for i in range(count):
  vertices,w,h=struct.unpack_from('<3I',world,at);n=12+vertices*40;key=struct.unpack_from('<5I',ids,8+i*20);result[key].append(world[at:at+n]);at+=n+w*h*4
 return result
def events(history):
 at=64
 while at<len(history):
  tag,n=struct.unpack_from('<2Q',history,at);assert n>=64 and at+n<=len(history)
  if tag==2:
   ordinal,refresh,asset,shade,texture=struct.unpack_from('<5Q',history,at+16);yield ordinal,refresh,texture,history[at+96:at+n]
  at+=n
 assert at==len(history)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';protected={str(p):sha(p) for p in [rom,state]};data=state.read_bytes();h=op(os.fsencode(rom));assert h and load(h,data,len(data))
for name in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn(core,'nfa_core_'+name,[P,I])(h,1)
assert enable(1)
api=API(C.sizeof(API),h,*[C.cast(getattr(core,'nfa_core_'+n),P).value for n in ['capture_layer_info','capture_background_scene','capture_source_world','capture_road_history','capture_wall_history','capture_write_ownership']],0);assert bind(C.byref(api))
start=(Q*4)();assert timing(h,start);pcm=(C.c_int16*8192)();audio_hash=hashlib.sha256();frame_hash=hashlib.sha256();samples=0;counts=collections.Counter();seen_owners=set();cache={};roots={};missing=[];rows=[];saved=None;all_stats=None
try:
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for index in range(600):
   assert step(h,1|(16 if 60<=index<120 else 0)|(32 if 480<=index<540 else 0))==1;image=C.string_at(pixels(h),153600);assert image==oracle.read(153600);frame_hash.update(image);tick=(Q*4)();assert timing(h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==start[2]+index+1 and tick[3]==index+1
   while True:
    n=audio(h,pcm,4096)
    if not n:break
    samples+=n;audio_hash.update(C.string_at(pcm,n*4))
   frame=capture(C.byref(api),64*1024*1024)
   if not frame:assert baseline['source_rows'][index] is None;continue
   try:
    fi=(Q*8)();assert frame_info(frame,fi);background=blob(component,frame,0,0);actual=[]
    for role in range(fi[4]):
     key=(Q*5)();assert owner(frame,role,key);parts=[background]+[blob(component,frame,role,k) for k in range(1,5)];actual.append(dict(owner=list(key),parts=[hashlib.sha256(p).hexdigest() for p in parts]));counts['source_owner_observations']+=1
     token=tuple(key)
     if token in seen_owners:continue
     seen_owners.add(token);world=surfaces(parts[1])
     for kind in [1,2]:
      for ordinal,refresh,texture,command in events(parts[kind+1]):
       counts['history_event_observations']+=1;event=(key[0],kind,ordinal)
       if event not in cache:
        n=read(*event,None,0)
        if not n:cache[event]=None;missing.append(dict(event=event,refresh=refresh));continue
        assert 196<n<=1488;result=C.create_string_buffer(n);assert read(*event,result,n)==n;raw=result.raw;words=struct.unpack_from('<16Q',raw);identity=struct.unpack_from('<5I',raw,128);cam=struct.unpack_from('<12i',raw,148);prefix=raw[196:];assert words[:4]==(key[0],kind,ordinal,refresh) and words[5]<=refresh and words[7]<=words[8] and words[9]==len(prefix) and words[10]==texture and words[11]==1 and words[12]==fnv(command) and words[13]==fnv(prefix) and words[14:]==(0,0) and identity[0]==kind
        vertex_count,w,height=struct.unpack_from('<3I',prefix);assert 3<=vertex_count<=32 and w and height and len(prefix)==12+vertex_count*40 and all(math.isfinite(v) for v in struct.unpack_from('<'+str(vertex_count*5)+'d',prefix,12));assert any(cam[:9])
        record=dict(words=list(words),identity=list(identity),camera=list(cam),prefix_hex=prefix.hex());roots[(words[0],words[4])]=record;cache[event]=(words,identity,prefix);rows.append(dict(event=event,root=words[4],refresh=refresh,command_hash=words[12]));counts['unique_valid_history_events']+=1;counts['kind_'+str(kind)]+=1;saved=(event,raw)
        sentinel=C.create_string_buffer(b'\xa5'*n,n)
        for bad in [(event[0]+1,kind,ordinal,n),(event[0],0,ordinal,n),(event[0],kind,0,n),(event[0],kind,ordinal,n-1)]:assert not read(bad[0],bad[1],bad[2],sentinel,bad[3]) and sentinel.raw==b'\xa5'*n;counts['atomic_guards']+=1
       record=cache[event]
       if record is None:counts['missing_event_observations']+=1;continue
       words,identity,prefix=record;assert words[3]==refresh and words[10]==texture and words[12]==fnv(command)
       candidates=world.get(identity,[])
       if candidates:
        counts['original_identity_present_in_current_packet']+=1
        if prefix in candidates:counts['exact_original_xyz_uv_prefix_matches']+=1
        else:counts['same_identity_different_xyz_uv_prefix']+=1
       else:counts['historical_identity_absent_current_packet']+=1
     cell_archive.writestr(str(key[1])+'/proof.bin',parts[4])
     for kind in [1,2]:
      n=owner_cells(key,kind,None,0);assert n==307264;destination=C.create_string_buffer(n);assert owner_cells(key,kind,destination,n)==n;raw=destination.raw;assert struct.unpack_from('<8Q',raw)==tuple(key)+(kind,38400,n);ordinals=struct.unpack_from('<38400Q',raw,64)
      cell_archive.writestr(str(key[1])+'/'+str(kind)+'-ordinals.bin',raw);cell_archive.writestr(str(key[1])+'/'+str(kind)+'-history.bin',parts[kind+1])
      proof=parts[4];assert all((proof[80+i]==kind)==bool(value) for i,value in enumerate(ordinals));counts['exact_proof_cell_slots']+=38400
      retained=retention(frame,role,kind+1,64*1024*1024);assert retained
      try:records=blob(retention_buffer,retained,1)
      finally:retention_free(retained)
      historical=present=0
      for cell,asset,offset,refresh in struct.iter_unpack('<4I',records):
       ordinal=ordinals[cell];assert ordinal;entry=cache[(key[0],kind,ordinal)];assert entry and entry[0][3]==refresh;words,identity,prefix=entry;counts['retained_cells_bound_to_original_source']+=1;counts['retained_cell_kind_'+str(kind)]+=1
       if identity in world:present+=1
       else:historical+=1
      counts['retained_cells_identity_absent_current_packet']+=historical;cell_rows.append(dict(owner=list(key),kind=kind,cells=len(records)//16,identity_present=present,identity_absent=historical))
      saved_cells=(list(key),kind,raw);sentinel=C.create_string_buffer(b'\xa5'*n,n);bad=(Q*5)(*key);bad[1]+=1
      for args in [(bad,kind,n),(key,0,n),(key,kind,n-1)]:assert not owner_cells(args[0],args[1],sentinel,args[2]) and sentinel.raw==b'\xa5'*n;counts['atomic_owner_cell_guards']+=1
      counts['immutable_owner_cell_maps']+=1
    assert actual==baseline['source_rows'][index],index;counts['source_frames_exact']+=1
   finally:free(frame)
 all_stats=(Q*8)();assert stats(all_stats);all_stats=list(all_stats);assert saved
 event,raw=saved;assert load(h,data,len(data));sentinel=C.create_string_buffer(b'\xa5'*len(raw),len(raw));assert not read(*event,sentinel,len(raw)) and sentinel.raw==b'\xa5'*len(raw);counts['epoch_reset_guard']+=1
 key,kind,cells=saved_cells;sentinel_cells=C.create_string_buffer(b'\xa5'*len(cells),len(cells));assert not owner_cells((Q*5)(*key),kind,sentinel_cells,len(cells)) and sentinel_cells.raw==b'\xa5'*len(cells);counts['owner_cell_reset_guard']+=1
 assert enable(0) and not read(*event,sentinel,len(raw));counts['disabled_guard']+=1
finally:cell_archive.close();enable(0);close(h)
assert samples==baseline['pcm_frames']==443007 and audio_hash.hexdigest()==baseline['pcm_sha256'] and frame_hash.hexdigest()==baseline['original_frames_sha256'];assert counts['kind_1'] and counts['kind_2'] and counts['exact_original_xyz_uv_prefix_matches']
(out/'provenance-roots.json').write_text(json.dumps(list(roots.values()),indent=2));(out/'provenance-events.json').write_text(json.dumps(rows,indent=2));(out/'owner-cell-report.json').write_text(json.dumps(cell_rows,indent=2));assert protected=={str(p):sha(p) for p in [rom,state]}
report=dict(result='PASS_READONLY_HISTORY_PROVENANCE_WITH_EXPLICIT_COVERAGE',core_sha256=build['core_sha256'],baseline_sha256=sha(baseline_path),test_sha256=sha(Path(__file__)),counts=dict(counts),unique_owners=len(seen_owners),unique_roots=len(roots),unique_missing=len(missing),missing_examples=missing[:12],observer_stats=all_stats,original_frames_exact=True,original_source_components_exact=True,original_pcm_sha256=audio_hash.hexdigest(),original_pcm_frames=samples,protected_sha256=protected,no_new_game_hooks=True,no_game_writes=True,full_scene_60fps=False,live_motion=False)
(out/'history-provenance-test-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True)
