"""Read-only layered replay to isolate the late background capture gaps."""
from pathlib import Path
import ctypes as C,hashlib,json,os,struct
source=Path('Y:\\CODEX\\NFSUG-Native-PC-Port\\work\\pc');root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=Path('C:\\NFSUG-Workspace\\NFSUG-pc-rotation-trace-core\\probe');out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();core_dir=base/'NFSUG-pc-rotation-trace-core'
build=json.loads((core_dir/'rotation-trace-build-report.json').read_text());assert sha(core_dir/'capture-host.dll')==build['core_sha256']
for n,h in build['maintained_source_sha256'].items():assert sha(source/n)==h,n
for k in ['NF_TEST_RACING_OWNED_CAPTURE','NF_LIVE_ROAD_ATTRIBUTES','NF_CAPTURE_MODEL_VIEWS','NF_TRACE_NATIVE_COMMANDS']:os.environ.pop(k,None)
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(core_dir/'capture-host.dll'))
P=C.c_void_p;Q=C.c_uint64;U=C.c_uint;S=C.c_size_t;I=C.c_int

def fn(name,args,result=I):f=getattr(d,name);f.argtypes=args;f.restype=result;return f
op=fn('nfa_core_open',[C.c_char_p],P);close=fn('nfa_core_close',[P],None);load=fn('nfa_core_load_state',[P,P,S]);step=fn('nfa_core_step',[P,U]);timing=fn('nfa_core_timing',[P,P]);pixels=fn('nfa_core_pixels',[P],P);audio=fn('nfa_core_read_audio',[P,P,S],S);info=fn('nfa_core_capture_layer_info',[P,P]);stats=fn('nfa_core_capture_wall_history_stats',[P,P])
reads={n:fn('nfa_core_capture_'+n,[P,Q,U,P,S],S) for n in ['bundle','sky_scene','background_scene','sky','provenance']}
wall=fn('nfa_core_capture_wall_history',[P,Q,U,U,U,P,S],S)
try:vram=fn('nf_native_live_background_vram',[U,P,U]);coverage=fn('nf_native_live_background_coverage',[U,P,U])
except AttributeError:vram=coverage=None
whole=fn('nfa_core_capture_display_owner',[P,U,P]);split=fn('nfa_core_capture_split',[P,U,P])
scene_stats=fn('nf_native_scene_stats',[P],None)
diag=fn('nfa_core_capture_scene_rejection_info',[P,P,S])
first=fn('nfa_core_capture_first_model_failure',[P,P,S])
trace_enable=fn('nfa_core_capture_rotation_trace_enable',[P,U]);trace_copy=fn('nfa_core_capture_rotation_trace_copy',[P,P,S],S)
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';statepath=root/'work/integration-0.state';state=statepath.read_bytes();before={str(p):sha(p) for p in (rom,statepath)}
h=op(os.fsencode(rom));assert h and load(h,state,len(state))
for n in ['capture_enable','capture_layers','capture_source_world_enable','capture_wall_history_enable','capture_sky_enable']:assert fn('nfa_core_'+n,[P,I])(h,1)
assert trace_enable(h,848)
initial=(Q*4)();assert timing(h,initial);pcm=(C.c_int16*8192)();rows=[];audiohash=hashlib.sha256();samples=0

def read(name,ep,serial):
 f=reads[name];n=f(h,ep,serial,None,0)
 if not n:return b''
 assert n<=64*1024*1024
 buf=C.create_string_buffer(n);assert f(h,ep,serial,buf,n)==n;return buf.raw
try:
 with (base/'NFSUG-android-capture-local/capture-off/frames.raw').open('rb') as oracle:
  for i in range(3550):
   phase=i%1200;assert step(h,1|(32 if 180<=phase<500 else 16 if 500<=phase<720 else 0))==1
   tick=(Q*4)();assert timing(h,tick) and tuple(tick[:2])==(16777216,280896) and tick[2]==initial[2]+i+1 and tick[3]==i+1
   # This route uses its separate full6000-step original-output oracle report.
   while True:
    n=audio(h,pcm,4096)
    if not n:break
    samples+=n;audiohash.update(C.string_at(pcm,n*4))
   if i+1<3500:continue
   meta=(Q*5)();assert info(h,meta);ep,refresh=meta[:2]
   packets={name:read(name,ep,refresh) for name in ['bundle','sky_scene','background_scene']}
   ws=(Q*8)();assert stats(h,ws)
   row=dict(logic_step=i+1,display=list(meta),lengths={n:len(p) for n,p in packets.items()},wall_stats=list(ws),owners=[])
   ns=(U*4)();scene_stats(ns);row['native_scene_stats']=list(ns)
   detail=(U*192)();assert diag(h,detail,192);row['rejection_detail']=list(detail[16:25]);row['first_bad_event']=list(detail[32:41]);row['model_detail']=list(detail[48:56])
   frozen=(U*256)();assert first(h,frozen,256) and tuple(frozen[:3])==(0x31424d4e,1,256);row['first_model_failure']=list(frozen)
   provenance=read('provenance',ep,refresh);assert len(provenance)==5312
   words=struct.unpack('<664Q',provenance);whole_id=(Q*8)();split_id=(Q*12)()
   row['whole_owner_matches']=bool(whole(h,refresh,whole_id));row['split_owner_matches']=bool(split(h,refresh,split_id))
   row['provenance_header']=list(words[:8]);row['retained_owner_metadata']=[list(words[8+j*8:16+j*8]) for j in range(2)]
   runs=[]
   for y in range(160):
    display,g0,g1,version=words[24+y*4:28+y*4];page=(display>>4)&1;values=(display,page,g0,g1,version)
    if runs and tuple(runs[-1]['values'])==values:runs[-1]['end_row']=y
    else:runs.append(dict(begin_row=y,end_row=y,values=list(values)))
   row['scanout_runs']=runs
   row['owner_join_checks']=[]
   for j in range(2):
    owner_epoch,serial,begin,end,page,generation,version,present=words[8+j*8:16+j*8]
    checks=dict(present=bool(present),epoch_matches=owner_epoch==ep,version_current=bool(version) and version==words[5],closed_before_display=refresh>=end)
    checks['display_mismatch_rows']=sum(((words[24+y*4]>>4)&1)!=page or (words[24+y*4]&7)!=4 or bool(words[24+y*4]&0x8080) for y in range(160))
    checks['generation_mismatch_rows']=sum(words[25+y*4+page]!=generation for y in range(160)) if page<=1 else 160
    checks['version_mismatch_rows']=sum(words[27+y*4]!=version for y in range(160))
    row['owner_join_checks'].append(checks)
   if not packets['background_scene'] and i+1 in [1947,1951]:(out/f'{i+1}-provenance.bin').write_bytes(provenance)
   bundle=packets['bundle'];sky=packets['sky_scene'];sh=struct.unpack_from('<16Q',sky) if sky else None
   if bundle:
    bh=struct.unpack_from('<16Q',bundle);assert 1<=bh[7]<=2
    for j in range(bh[7]):
     at,nb=bh[8+j*2:10+j*2];head=struct.unpack_from('<8I',bundle,at);assert head[0]==0x3150534e
     serial,begin,end,page=head[4:8];o=dict(serial=serial,begin=begin,end=end,page=page,wall_bytes=wall(h,ep,serial,begin,end,None,0))
     rawsky=read('sky',ep,serial);o['raw_sky_bytes']=len(rawsky)
     if rawsky:o['raw_sky_header']=list(struct.unpack_from('<14I',rawsky))
     vr=C.create_string_buffer(0x18000);cv=C.create_string_buffer(0x18000);closed=end+1
     o['background_vram_available']=bool(vram(closed,vr,0x18000)) if vram else None;o['background_coverage_available']=bool(coverage(closed,cv,0x18000)) if coverage else None
     if o['background_vram_available'] and o['background_coverage_available']:
      vb=vr.raw[page*0xa000:page*0xa000+38400];cb=cv.raw[page*0xa000:page*0xa000+38400]
      o['coverage_invalid_cells']=sum(x>1 for x in cb);o['coverage_present_cells']=sum(x!=0 for x in cb)
      if sh:
       sky_at=sh[10+j*2];source=sky[sky_at+56:sky_at+56+15136]
       o['sky_uncovered_cells']=sum(not x for x in cb[10560:25696]);o['sky_mismatched_cells']=sum(a!=b for a,b in zip(vb[10560:25696],source))
     row['owners'].append(o)
   if not packets['background_scene']:
    for name,p in packets.items():
     if p and i+1 in [1947,1951]:(out/f'{i+1}-{name}.bin').write_bytes(p)
   rows.append(row)
   after=(Q*4)();assert timing(h,after) and tuple(after)==tuple(tick)
 trace_bytes=trace_copy(h,None,0);assert 64<trace_bytes<=64+256*256
 trace_buffer=C.create_string_buffer(b'X'*trace_bytes,trace_bytes);assert trace_copy(h,trace_buffer,trace_bytes-1)==0 and trace_buffer.raw==b'X'*trace_bytes
 assert trace_copy(h,trace_buffer,trace_bytes)==trace_bytes
 data=trace_buffer.raw;(out/'rotation-trace.bin').write_bytes(data);header=struct.unpack_from('<16I',data)
 assert header[:2]==(0x3154524e,1) and header[6]==848 and header[2]*4==len(data) and header[9]==64
 records=[list(struct.unpack_from('<64I',data,64+i*256)) for i in range(header[3])]
 (out/'rotation-events.json').write_text(json.dumps(dict(header=list(header),records=records),indent=2))
 assert load(h,state,len(state)) and trace_copy(h,None,0)==0
finally:close(h)
assert before=={str(p):sha(p) for p in (rom,statepath)}
failures=[r for r in rows if not r['lengths']['background_scene']]
report=dict(result='BACKGROUND_GAP_LAYERED_PROBE_COMPLETE',steps=3550,window=[3500,3550],failures=failures,rows=rows,first600_original_pixels_exact=None,game_clocks_exact=True,no_diagnostic_logic_steps=True,audio_frames=samples,audio_sha256=audiohash.hexdigest(),rom_state_sha256=before,core_sha256=sha(core_dir/'capture-host.dll'),script_sha256=sha(Path(__file__)),full_scene_60fps=False,scope='Read-only replay; diagnostic reads add work and are not a performance measurement.')
(out/'background-gap-probe-report.json').write_text(json.dumps(report,indent=2))
print('ROTATION_TRACE_CAPTURED',header[3],'records',trace_bytes,'bytes')
