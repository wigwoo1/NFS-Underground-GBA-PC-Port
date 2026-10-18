"""Identical-ledger CPU timing and full-RAM parity with capture isolated."""
from pathlib import Path
import ctypes as C,json,time,statistics,hashlib,os,sys
root=Path('work/camera').resolve();report=Path(sys.argv[1]);mode=sys.argv[2];r=json.loads(report.read_text())
if mode.startswith('capture'):
 setup=(root/'capture_motion_scanline_state.py').read_text().split('gpu=None;gpu_worker=None;gpu_checks=[]')[0];setup=setup.replace('visibility-probe-wide.dll',sys.argv[3]) if len(sys.argv)>3 else setup;exec(compile(setup,'capture_setup','exec'))
 for k in list(os.environ):
  if k.startswith('NF_') and k!='NF_TEST_RACING_OWNED_CAPTURE':os.environ.pop(k,None);assert crt._putenv((k+'=').encode())==0
else:
 crt=C.CDLL('msvcrt');crt._putenv.argtypes=[C.c_char_p]
 for k in list(os.environ):
  if k.startswith('NF_'):os.environ.pop(k,None);assert crt._putenv((k+'=').encode())==0
 rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');state=root.parent/'race.state'
 dll=root.parent/'nfsprobe.dll' if mode=='original' else root/'visibility-probe-wide.dll'
 d=C.CDLL(str(dll));d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint]
protected={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in (rom,state,root.parent/'nfsprobe.dll')}
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0)
debug_start=int(os.environ.get('NFS_DEBUG_START_REFRESH','8804'));assert debug_start>0
cost=[];checks=[];event_profile=[];native_profile=None;arm_stages=None;frame_hashes=[];last_frame=0;debug_rows=[];region_debug=None;debug_memory=[]
try:
 if mode.startswith('capture'):
  assert d.nf_native_scene_sink(text_scene_sink,None);owned_rom=rom.read_bytes();assert d.nf_live_visibility_enable(owned_rom,len(owned_rom),16*1024*1024);assert d.nf_bitmap_text_enable(1)
 for row in r['startup_inputs']:
  if mode.startswith('capture') and row['refresh']==8749:
   assert d.nf_world_trace(b'') and d.nf_layer_queue_enable(1);assert d.nf_owned_graph_live_enable(1);assert d.nf_native_model_plan_trace(b'',model_plan_table,len(model_plan_table))
  d.nf_frame(row['keys'])
 if mode=='capture-no-graph':assert d.nf_owned_graph_live_enable(0)
 if mode=='capture-no-model':d.nf_native_model_plan_trace(None,None,0)
 if mode=='capture-no-layers':assert d.nf_layer_queue_enable(0)
 if mode=='capture-no-arm':d.nf_scene_enable(0)
 if mode=='capture-profile':d.nf_capture_profile_enable(1)
 if mode=='capture-arm-stages':d.nf_arm_stage_profile_enable(1)
 for row in r['inputs']:
  if mode=='capture-region-debug' and row['refresh']>=debug_start and region_debug is None:
   region_debug=str(report.with_suffix('.regions.bin'));d.nf_owned_region_entry_trace.argtypes=[C.c_char_p];assert d.nf_owned_region_entry_trace(region_debug.encode())
  if mode in ('capture-wall-debug','capture-wall-scratch','capture-wall-call') and row['refresh']==debug_start:
   d.nf_debug(0x03000304 if mode=='capture-wall-call' else 0x03002734 if mode=='capture-wall-scratch' else 0x0300272c)
   if mode=='capture-wall-scratch':assert d.nf_debug_memory_config(5,52)
  began=time.perf_counter_ns();d.nf_frame(row['keys']);cost.append(time.perf_counter_ns()-began)
  if mode=='capture-frame-parity':
   candidate=d.nf_native_live_latest_frame()
   if candidate>last_frame and candidate<=d.nf_layer_queue_latest():
    n=C.c_size_t();assert d.nf_native_owned_frame_read(d.nf_native_scene_epoch(),candidate,None,0,C.byref(n));out=C.create_string_buffer(n.value);assert d.nf_native_owned_frame_read(d.nf_native_scene_epoch(),candidate,out,n.value,C.byref(n));frame_hashes.append(dict(refresh=candidate,bytes=n.value,sha256=hashlib.sha256(out.raw).hexdigest()));last_frame=candidate
 if mode=='capture-profile':
  totals=(C.c_uint64*6)();assert d.nf_capture_profile_read(totals);native_profile=list(totals)
  for index in range(64):
   item=(C.c_uint64*3)()
   if d.nf_capture_event_profile_read(index,item):event_profile.append(dict(pc=hex(item[0]),calls=item[1],ns=item[2]))
 if mode=='capture-arm-stages':
  totals=(C.c_uint64*6)();assert d.nf_arm_stage_profile_read(totals);arm_stages=dict(zip(('native_scene_ns','native_scene_calls','world_trace_ns','world_trace_calls','legacy_scene_ns','legacy_scene_calls'),totals))
 if mode=='capture-region-debug':d.nf_owned_region_entry_trace(None)
 if mode in ('capture-wall-debug','capture-wall-scratch','capture-wall-call'):
  d.nf_debug_data.restype=C.POINTER(C.c_uint);n=C.c_int();ptr=d.nf_debug_data(C.byref(n));debug_rows=[list(ptr[i*16:(i+1)*16]) for i in range(n.value)]
 if mode=='capture-wall-scratch':
  d.nf_debug_memory_data.restype=C.c_void_p;count=C.c_uint();width=C.c_uint();ptr=d.nf_debug_memory_data(C.byref(count),C.byref(width));assert width.value==52;debug_memory=[C.string_at(ptr+i*256,width.value).hex() for i in range(count.value)]
 for name,address,n in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  target=report.with_suffix('.profile-'+mode+'-'+name+'.bin');d.nf_dump(str(target).encode(),address,n);assert target.read_bytes()==Path(r['final_ram'][name]['path']).read_bytes();checks.append(dict(region=name,bytes=n,exact=True))
finally:d.nf_close()
assert all(hashlib.sha256(Path(x).read_bytes()).hexdigest()==v for x,v in protected.items())
result=dict(result='PASS_IDENTICAL_LEDGER_CAPTURE_PROFILE',mode=mode,debug_start_refresh=debug_start,debug_memory=debug_memory,region_debug=region_debug,debug_rows=debug_rows,frame_hashes=frame_hashes,arm_stages=arm_stages,event_profile=event_profile,native_profile=native_profile,updates=len(cost),total_ms=sum(cost)/1e6,median_ms=statistics.median(cost)/1e6,max_ms=max(cost)/1e6,checks=checks,scope='Same ledger CPU nf_frame duration, no GPU/read/producer or pacing; fullRAM exact. Short interval, not60fps gameplay proof.')
report.with_suffix('.profile-'+mode+'.json').write_text(json.dumps(result,indent=2));print(result)
