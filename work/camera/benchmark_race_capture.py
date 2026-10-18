"""Fixed 300-update capture benchmark; component timing, never gameplay proof."""
from pathlib import Path
import ctypes as C, json, hashlib, time, statistics, subprocess, sys, os, struct
from project_paths import load_session
p=Path(__file__).resolve().parent
if len(sys.argv)==1:
 reports=[]
 for mode in ['baseline','bus','direct','bus','direct']:
  run=subprocess.run([sys.executable,str(Path(__file__).resolve()),mode],capture_output=True,text=True,timeout=60)
  assert run.returncode==0,run.stdout+run.stderr
  reports.append(json.loads(run.stdout.split('BENCHMARK_JSON=')[-1]))
 assert len({tuple(x['ram_sha256']) for x in reports})==1
 result=dict(result='PASS_COMPONENT_STATE',runs=reports,original_ram_exact=True,scope='Fixed original input updates without GPU, presentation scheduling or physical Xbox; no full-scene60fps proof')
 (p/'race-capture-benchmark.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2));sys.exit()
updates=int(os.environ.get('BENCH_UPDATES','300'));assert updates in (300,720)
live_route=os.environ.get('BENCH_LIVE_ROUTE')=='1'
mode=sys.argv[1];assert mode in ['baseline','bus','direct','direct-profile','direct-dirty','direct-dirty-verify','direct-dirty-profile']
for k in list(os.environ):
 if k.startswith('NF_'):os.environ.pop(k)
crt=C.CDLL('msvcrt');crt._putenv_s.argtypes=[C.c_char_p,C.c_char_p]
flags=['NF_CAPTURE_MODEL_VIEWS','NF_CAPTURE_WALL_OUTPUT_INDICES','NF_TEST_INDEXED_ENTRANTS','NF_TEST_RACING_OWNED_CAPTURE','NF_CAPTURE_RETAINED_STRIP','NF_CAPTURE_INDEXED_COPY','NF_TEST_NATIVE_BITMAP_TEXT']
if mode.startswith('direct'):flags+=['NF_TEST_DIRECT_CAPTURE_RAM']
if mode.startswith('direct-dirty'):flags+=['NF_LAYER_DIRTY']
if mode=='direct-dirty-verify':flags+=['NF_VERIFY_LAYER_DIRTY']
if os.environ.get('BENCH_NF_TEST_WALL_SHADE_LOOKUP_CACHE')=='1':flags.append('NF_TEST_WALL_SHADE_LOOKUP_CACHE')
if os.environ.get('BENCH_NF_VERIFY_WALL_PLAN_REUSE')=='1':flags.append('NF_VERIFY_WALL_PLAN_REUSE')
for option in ('NF_TEST_SURFACE_READ_REUSE','NF_VERIFY_SURFACE_READ_REUSE'):
 if os.environ.get('BENCH_'+option)=='1':flags.append(option)
for option in ('NF_TEST_DIRECT_CAPTURE_ROM','NF_TEST_VERIFY_CAPTURE_ROM'):
 if os.environ.get('BENCH_'+option)=='1':flags.append(option)
for flag in flags:assert crt._putenv_s(flag.encode(),b'1')==0
session=load_session(p/'prototype-runs/threaded-prepared-59aee71d90ee4c88a494da1a6b97ea61-session.json')
state=p.parent/'race.state';before=hashlib.sha256(state.read_bytes()).hexdigest()
d=C.CDLL(str(p.parent/'nfsprobe.dll' if mode=='baseline' else p/'visibility-probe-wide.dll'))
P=C.c_void_p;Z=C.c_size_t;d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_dump.argtypes=[C.c_char_p,C.c_uint,C.c_uint]
assert d.nf_init(session['rom'].encode(),b'') and d.nf_state(str(state).encode(),0)
completed=[];Sink=C.CFUNCTYPE(C.c_int,P,C.c_uint64,P,Z)
@Sink
def sink(ctx,e,data,size):completed.append((e,struct.unpack_from('<I',C.string_at(data,20),16)[0]));return 1
try:
 if mode!='baseline':
  rom=Path(session['rom']).read_bytes();d.nf_live_visibility_enable.argtypes=[P,Z,Z];d.nf_native_scene_sink.argtypes=[Sink,P]
  d.nf_page_write_audit_enable(1);d.nf_page_write_audit_generation_reset()
  assert d.nf_native_scene_sink(sink,None) and d.nf_native_scene_multimodel(1)
  assert d.nf_live_visibility_enable(rom,len(rom),16*1024*1024)
  d.nf_live_surface_audit_enable(1);assert d.nf_bitmap_text_enable(1) and d.nf_layer_queue_enable(1)
 profiled=mode in ('direct-profile','direct-dirty-profile');capture_totals=[0]*6
 if profiled:
  d.nf_capture_profile_enable(1);d.nf_capture_profile_read.argtypes=[C.c_void_p];d.nf_capture_event_profile_read.argtypes=[C.c_uint,C.c_void_p]
 ticks=[];cpu_begin=time.process_time_ns();begin=time.perf_counter_ns()
 for i in range(updates):
  start=time.perf_counter_ns();d.nf_frame(1|(32 if 180<=i<(500 if live_route else 240) else 16 if (500 if live_route else 240)<=i<(720 if live_route else updates) else 0));ticks.append((time.perf_counter_ns()-start)/1e6)
  if profiled:
   values=(C.c_uint64*6)();assert d.nf_capture_profile_read(values)
   capture_totals=[a+b for a,b in zip(capture_totals,values)]
 elapsed=(time.perf_counter_ns()-begin)/1e6;cpu=(time.process_time_ns()-cpu_begin)/1e6;digests=[]
 for name,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  out=p/('benchmark-'+mode+'-'+name+'.bin');d.nf_dump(str(out).encode(),address,size);digests.append(hashlib.sha256(out.read_bytes()).hexdigest())
 assert hashlib.sha256(state.read_bytes()).hexdigest()==before
 phases=[dict(begin=i,end=min(i+180,updates),wall_ms=sum(ticks[i:i+180]),over_budget=sum(x>280896/16777216*1000 for x in ticks[i:i+180])) for i in range(0,updates,180)]
 ticks.sort();report=dict(completion_ledger=completed,phases=phases,live_route=live_route,mode=mode,updates=updates,wall_ms=elapsed,cpu_ms=cpu,median_ms=statistics.median(ticks),p95_ms=ticks[int((len(ticks)-1)*.95)],max_ms=max(ticks),over_original_budget=sum(x>280896/16777216*1000 for x in ticks),completions=len(completed),ram_sha256=digests,save_unchanged=True)
 if os.environ.get('BENCH_NF_TEST_SURFACE_READ_REUSE')=='1':
  reuse=(C.c_uint64*3)();d.nf_live_surface_read_reuse_stats(reuse)
  assert reuse[0]>0 and reuse[2]==0
  if os.environ.get('BENCH_NF_VERIFY_SURFACE_READ_REUSE')=='1':assert reuse[1]==reuse[0]
  report['surface_read_reuse_stats']=list(reuse)
 if os.environ.get('BENCH_NF_VERIFY_WALL_PLAN_REUSE')=='1':
  plan=(C.c_uint32*5)();geometry=(C.c_uint32*5)()
  d.nf_live_wall_plan_stats(plan);d.nf_live_region_geometry_stats(geometry)
  assert plan[0]>0 and plan[1]>0 and plan[3]==0 and plan[4]==0 and geometry[4]>0,(list(plan),list(geometry))
  report.update(wall_plan_stats=list(plan),region_geometry_stats=list(geometry),saved_input_plan_reuse_verified=True)
 if mode.startswith('direct-dirty'):
  stats=(C.c_uint64*3)();d.nf_layer_snapshot_dirty_stats.argtypes=[C.c_void_p];d.nf_layer_snapshot_dirty_stats(stats);assert stats[2]==0
  if mode=='direct-dirty-verify':assert stats[1]>0
  baseline=json.loads(os.environ['BENCH_BASELINE_JSON']) if os.environ.get('BENCH_BASELINE_JSON') else json.loads((p/'race-capture-benchmark.json').read_text())['runs'][0];assert report['ram_sha256']==baseline['ram_sha256'] and (updates!=300 or report['completions']==75),(report,baseline)
  report.update(dirty_stats=list(stats),original_ram_exact=True)
  (p/('race-capture-'+mode+'.json')).write_text(json.dumps(report,indent=2))
 if profiled:
  events=[]
  for index in range(64):
   values=(C.c_uint64*3)()
   if not d.nf_capture_event_profile_read(index,values):break
   events.append(dict(pc=hex(values[0]),calls=values[1],wall_ms=values[2]/1e6))
  events.sort(key=lambda x:x['wall_ms'],reverse=True)
  surface=(C.c_uint64*4)();d.nf_live_surface_capture_profile_read.argtypes=[C.c_void_p];assert d.nf_live_surface_capture_profile_read(surface)
  baseline=json.loads(os.environ['BENCH_BASELINE_JSON']) if os.environ.get('BENCH_BASELINE_JSON') else json.loads((p/'race-capture-benchmark.json').read_text())['runs'][0]
  assert report['ram_sha256']==baseline['ram_sha256'] and (updates!=300 or report['completions']==75),(report,baseline)
  rom_stats=(C.c_uint64*3)();d.nf_capture_rom_copy_stats.argtypes=[C.c_void_p];d.nf_capture_rom_copy_stats(rom_stats);assert rom_stats[2]==0
  shade_stats=(C.c_uint64*2)();d.nf_wall_shade_lookup_stats.argtypes=[C.c_void_p];d.nf_wall_shade_lookup_stats(shade_stats)
  volume=(C.c_uint64*3)();d.nf_live_surface_capture_bytes_read.argtypes=[C.c_void_p];assert d.nf_live_surface_capture_bytes_read(volume)
  report.update(rom_copy_stats=list(rom_stats),wall_shade_lookup_stats=list(shade_stats),surface_hash_bytes=dict(road=volume[0],wall=volume[1],lighting=volume[2]),original_ram_exact=True,capture_totals=capture_totals,events=events,surface_capture_ns=list(surface),scope='Fixed input component profiling; event timing includes timer overhead, totals aggregate frame resets; no live60fps proof')
  (p/('race-capture-'+mode+'.json')).write_text(json.dumps(report,indent=2))
  if mode=='direct-profile':(p/'race-capture-profile.json').write_text(json.dumps(report,indent=2))
 print('BENCHMARK_JSON='+json.dumps(report))
finally:d.nf_close()




