"""Original-input paced endpoint diagnostic without scanline export or hot-path RGB checks."""
from pathlib import Path
import ctypes as C,time,json,hashlib,sys
from live_owned_gpu_worker import LiveOwnedGPUWorker
from live_game_controls import LiveGameControls
# Reuse only bindings/input/protection setup, never its diagnostic capture loop.
setup=Path('work/camera/capture_motion_scanline_state.py').read_text().split('gpu=None;gpu_worker=None;gpu_checks=[]')[0]
exec(compile(setup,'capture_setup','exec'))
for k in list(os.environ):
 if k.startswith('NF_') and k!='NF_TEST_RACING_OWNED_CAPTURE':os.environ.pop(k,None);assert crt._putenv((k+'=').encode())==0
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0);assert d.nf_native_scene_sink(text_scene_sink,None)
rom_owned=rom.read_bytes();assert d.nf_live_visibility_enable(rom_owned,len(rom_owned),16*1024*1024);assert d.nf_bitmap_text_enable(1)
pause_test='--pause-test' in sys.argv;pause_checks=[];pause_injected=False
no_world_files='--no-world-files' in sys.argv
no_plan_files='--no-plan-files' in sys.argv or no_world_files
limit_test='--exhaust-diagnostics' in sys.argv
if limit_test:
 d.nf_world_trace_limit.argtypes=[C.c_uint];d.nf_world_trace_limit(0)
long_capture='--long-capture' in sys.argv
all_scenes='--all-scenes' in sys.argv or long_capture;capture_stop=0xffffffff if long_capture else 8830 if all_scenes else 8781
d.nf_native_live_latest_frame.restype=C.c_uint;d.nf_native_live_scene_count.restype=C.c_uint
worker=LiveOwnedGPUWorker(d.nf_native_scene_epoch(),draw_only=True,present=True,paced=True,verify=False,delay_refreshes=4,expected_frames=None if all_scenes or pause_test else 7)
targets=[8758,8762,8766,8769,8773,8776,8780];captured=[];origin=None;started=False;startup=None;scene_count=0;capture_closed=False;simulation=[];frame_cost=[];frame=C.create_string_buffer(0x1000000)
game_controls=LiveGameControls(worker,d.nf_frame,d.nf_native_scene_refresh,snapshot=lambda:dict(keys=int(row['keys']),paused=False,quit=False))
try:
 for row in rows:
  before=d.nf_native_scene_refresh()
  if before>=8749 and not started:
   assert d.nf_world_trace(b'' if no_world_files else b'NUL');assert d.nf_layer_queue_enable(1)
   assert d.nf_native_model_plan_trace(b'' if no_plan_files else str(p/'light-live-plans.bin').encode(),model_plan_table,len(model_plan_table))
   started=True;startup_begin=time.perf_counter_ns()
  if pause_test and origin is not None and not pause_injected and before>=8763:
   worker.set_paused(True);pause_injected=True
   snapshots=[]
   for when in ('before','after'):
    parts=[]
    for name,address,n in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
     target=p/f'pause-{when}-{name}.bin';d.nf_dump(str(target).encode(),address,n);parts.append(target.read_bytes())
    snapshots.append(b''.join(parts))
    if when=='before':time.sleep(.15)
   assert snapshots[0]==snapshots[1] and d.nf_native_scene_refresh()==before
   worker.set_paused(False);origin=worker.clock_origin
   pause_checks.append(dict(refresh=before,original_ram_unchanged=True,frozen_bytes=len(snapshots[0]),pause_ns=worker.pause_events[-1]['duration_ns']))
  if origin is not None:
   ticks=(before-base+1)*280896;deadline=origin+(ticks*1000000000+16777215)//16777216;worker.wait_until(deadline)
   simulation.append(dict(refresh=before,deadline_ns=deadline,begin_ns=time.perf_counter_ns()))
  assert game_controls.step()
  candidate=d.nf_native_live_latest_frame() if all_scenes else (targets[len(captured)] if len(captured)<len(targets) and d.nf_native_scene_refresh()>=targets[len(captured)]+1 else 0)
  if candidate and (not captured or candidate>captured[-1]) and candidate<=d.nf_layer_queue_latest():
   refresh=candidate;epoch=d.nf_native_scene_epoch();begin=time.perf_counter_ns();size=C.c_size_t()
   assert d.nf_native_owned_frame_read(epoch,refresh,None,0,C.byref(size))
   assert d.nf_native_owned_frame_read(epoch,refresh,frame,len(frame),C.byref(size));worker.submit(frame,size.value)
   if '--frame-diff' in sys.argv and refresh==8758:(p/('budget-zero-frame.bin' if limit_test else 'budget-normal-frame.bin')).write_bytes(frame.raw[:size.value])
   frame_cost.append(dict(refresh=refresh,assembly_submit_ns=time.perf_counter_ns()-begin,bytes=size.value,owned_sha256=hashlib.sha256(frame.raw[:size.value]).hexdigest() if '--frame-hashes' in sys.argv else None));captured.append(refresh)
   if origin is None:
    assert worker.first_frame_ready.wait(30) and not worker.errors
    startup=dict(first_live_refresh=refresh,load_ns=time.perf_counter_ns()-startup_begin)
    origin=time.perf_counter_ns();base=d.nf_native_scene_refresh();worker.start_clock(origin,base)
  if origin is not None and before>=capture_stop and not capture_closed:
   scene_count=d.nf_native_live_scene_count();capture_closed=True;d.nf_native_model_plan_trace(None,None,0);d.nf_world_trace(None)
 assert len(captured)>=7 if all_scenes else captured==targets
 if long_capture:scene_count=d.nf_native_live_scene_count()
 if all_scenes:assert len(captured)==scene_count,(len(captured),scene_count)
 for name,base_addr,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
  target=p/f'light-paced-{name}.bin';d.nf_dump(str(target).encode(),base_addr,size);assert target.read_bytes()==Path(str(source)+'-'+name+'.bin').read_bytes()
finally:
 worker.close();d.nf_native_model_plan_trace(None,None,0);d.nf_world_trace(None);d.nf_close()
assert all(hashlib.sha256(Path(x).read_bytes()).hexdigest()==v for x,v in protected.items())
r=dict(result='LIGHTWEIGHT_ORIGINAL_CLOCK_ENDPOINT_DIAGNOSTIC',simulation=simulation,presentation=worker.results,frame_cost=frame_cost,original_final_ram_exact=True,readback_in_hot_path=False,pause_checks=pause_checks,pause_events=worker.pause_events,startup=startup,completed_scene_count=scene_count,captured_scenes=captured,delay_refreshes=worker.delay_refreshes,scope='First actual live scene initializesGPU before starting wallclock atretained refresh. Remaining updates paced originalcycle ratio, fourrefresh presentationdelay. No interpolation/physicalXbox proof; native source trace writes remain.')
r['max_simulation_lateness_ns']=max(x['begin_ns']-x['deadline_ns'] for x in simulation);r['max_presentation_lateness_ns']=max(x['present_begin_ns']-x['presentation_deadline_ns'] for x in worker.results if x['presentation_deadline_ns'] is not None)
(p/('fully-fileless-owned-capture-tests.json' if no_world_files else 'fileless-owned-capture-tests.json' if no_plan_files else 'exhausted-diagnostic-capture-tests.json' if limit_test else 'long-owned-capture-tests.json' if long_capture else 'live-owned-pause-clock-tests.json' if pause_test else 'all-scenes-owned-paced-tests.json' if all_scenes else 'lightweight-owned-paced-tests.json')).write_text(json.dumps(r,indent=2));print(dict(result=r['result'],max_simulation_lateness_ms=r['max_simulation_lateness_ns']/1e6,max_presentation_lateness_ms=r['max_presentation_lateness_ns']/1e6,frame_assembly_ms=[round(x['assembly_submit_ns']/1e6,2) for x in frame_cost]))
