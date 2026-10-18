"""Experimental source-owned native gameplay host with optional pose interpolation."""
from pathlib import Path
import ctypes as C,time,json,hashlib,sys,argparse,threading
from live_owned_gpu_worker import LiveOwnedGPUWorker
from live_game_controls import LiveGameControls
from owned_thread_cycles import read as thread_cycles
# Spawned preparation workers import modules without starting another game host.
if __name__ != '__mp_main__':
 args=argparse.ArgumentParser();args.add_argument('--capture-probe-candidate',choices=('viewport-sky-capture-probe.dll',),default=None);args.add_argument('--smoke-initial-pause',action='store_true');args.add_argument('--shared-output-dedup',action='store_true');args.add_argument('--native-road-reader',action='store_true');args.add_argument('--present-completion-barrier',action='store_true');args.add_argument('--batch-gpu-fences',action='store_true');args.add_argument('--batch-gpu-timestamps',action='store_true');args.add_argument('--native-notification-queue',action='store_true');args.add_argument('--native-capture-batch',action='store_true');args.add_argument('--verify-native-capture-batch',action='store_true');args.add_argument('--native-capture-boundary',action='store_true');args.add_argument('--native-producer-wait',action='store_true');args.add_argument('--preparation-process-below-normal',action='store_true');args.add_argument('--capture-update-profile',action='store_true');args.add_argument('--original-update-boundary',action='store_true');args.add_argument('--producer-cycles',action='store_true');args.add_argument('--sky-renderer-candidate',choices=('owned-sky-gpu-pingpong.dll',),default=None);args.add_argument('--gpu-query-only',action='store_true');args.add_argument('--native-commit-stages',action='store_true');args.add_argument('--boundary-cpu',action='store_true');args.add_argument('--experimental-audio',action='store_true');args.add_argument('--audio-device-position',action='store_true');args.add_argument('--preparation-cache-range',type=int,nargs=2,default=None);args.add_argument('--show-smoke-window',action='store_true');args.add_argument('--swap-interval',type=int,choices=(0,1),default=None);args.add_argument('--smoke-seconds',type=float,default=0);args.add_argument('--diagnostic-wall-frames',type=int,default=0);args.add_argument('--diagnostic-scene-thresholds',type=int,nargs='+',default=None);args.add_argument('--regenerate-walls',action='store_true');args.add_argument('--graph-snapshots',action='store_true');args.add_argument('--interpolate',action='store_true');args.add_argument('--smoke-pause',action='store_true');args.add_argument('--smoke-steering',action='store_true');args.add_argument('--smoke-physical-controller',action='store_true');args.add_argument('--smoke-repeat-pause',action='store_true');args.add_argument('--smoke-quit-paused',action='store_true');args.add_argument('--gpu-finish',action='store_true');args.add_argument('--gpu-async-timer',action='store_true');args.add_argument('--gc-trace',action='store_true');args.add_argument('--bus-capture-rom',action='store_true');args.add_argument('--direct-capture-rom',action='store_true');args.add_argument('--verify-capture-rom',action='store_true');args.add_argument('--direct-capture-ram',action='store_true');args.add_argument('--bus-capture-ram',action='store_true');args.add_argument('--full-scene',action='store_true');args.add_argument('--background-prepare',action='store_true');args.add_argument('--profile-preparation-refresh',type=int,default=None);args.add_argument('--presentation-delay-refreshes',type=int,default=None);args.add_argument('--python-thread-switch-ms',type=float,default=None);args.add_argument('--shared-process-output',action='store_true');args.add_argument('--process-native-frame-join',action='store_true');args.add_argument('--thread-native-frame-join',action='store_true');args.add_argument('--renderer-thread-priority',type=int,choices=(0,1),default=0);args.add_argument('--process-prepare',action='store_true');args.add_argument('--precompute-world-samples',action='store_true');args.add_argument('--diagnostic-model-poses',action='store_true');args.add_argument('--diagnostic-model-scenes',type=int,default=0);args.add_argument('--model-scene-min-refresh',type=int,default=9950);args.add_argument('--model-scene-step',type=int,default=30);args.add_argument('--native-present-callback',action='store_true');args.add_argument('--capture-sky',action='store_true');args.add_argument('--diagnostic-sky-wraps',type=int,default=0);args.add_argument('--interpolate-sky',action='store_true');args.add_argument('--attach-sky',action='store_true');args.add_argument('--native-sky-inplace',action='store_true');args.add_argument('--continuous-sky',action='store_true');args.add_argument('--startup-readiness',action='store_true');args.add_argument('--progress-file',default=None);args.add_argument('--smoke-state',default='work/race.state');opt=args.parse_args();assert 0<=opt.smoke_seconds<=120;assert not opt.smoke_physical_controller or opt.smoke_seconds>0;assert not (opt.smoke_physical_controller and opt.smoke_steering)
 progress_path=Path(opt.progress_file).resolve() if opt.progress_file else None
 if progress_path is not None:
  progress_root=Path('work/camera/prototype-runs').resolve()
  if not progress_path.is_relative_to(progress_root):raise ValueError('Diagnostic progress file must be inside work/camera/prototype-runs')
  progress_path.parent.mkdir(parents=True,exist_ok=True)
 def progress(stage, **fields):
  if progress_path is None:return
  payload=dict(stage=stage,monotonic_ns=time.perf_counter_ns(),**fields)
  with progress_path.open('a',encoding='utf-8') as stream:
   stream.write(json.dumps(payload)+'\n')
   stream.flush()
 def compact_run_summary(rows,submit_rows,updates,scene_submissions,live_ns,live_begin_ns):
  import statistics
  shown=[r for r in rows if r.get('hidden_window_presented') and isinstance(r.get('present_begin_ns'),int) and r['present_begin_ns']>=live_begin_ns]
  begins=[r['present_begin_ns'] for r in shown]
  intervals=[(b-a)/1e6 for a,b in zip(begins,begins[1:])]
  lateness=[(r['present_begin_ns']-r['presentation_deadline_ns'])/1e6 for r in shown if isinstance(r.get('presentation_deadline_ns'),int)]
  present_calls=[(r['present_end_ns']-r['present_begin_ns'])/1e6 for r in shown if isinstance(r.get('present_end_ns'),int)]
  waits=[r.get('space_wait_ns',0)/1e6 for r in submit_rows if isinstance(r.get('space_wait_ns'),int)]
  def metrics(values):
   if not values:return dict(count=0,median_ms=None,p95_ms=None,max_ms=None,over20ms=0,over25ms=0,over33ms=0)
   ordered=sorted(values);n=len(ordered)
   return dict(count=n,median_ms=statistics.median(ordered),p95_ms=ordered[int(.95*(n-1))],max_ms=ordered[-1],over20ms=sum(x>20 for x in ordered),over25ms=sum(x>25 for x in ordered),over33ms=sum(x>33 for x in ordered))
  gaps=[]
  for index,(older,newer) in enumerate(zip(shown,shown[1:])):
   interval_ms=(newer['present_begin_ns']-older['present_begin_ns'])/1e6
   if interval_ms>20:
    submitted=newer.get('source_submitted_ns');dequeued=newer.get('source_dequeued_ns');present_end=newer.get('present_end_ns')
    gaps.append(dict(interval_ms=interval_ms,post_previous_present_ms=(newer.get('slot_begin_ns')-older.get('present_end_ns'))/1e6 if isinstance(newer.get('slot_begin_ns'),int) and isinstance(older.get('present_end_ns'),int) else None,post_present_record_ms=(older.get('present_record_done_ns')-older.get('present_end_ns'))/1e6 if isinstance(older.get('present_record_done_ns'),int) and isinstance(older.get('present_end_ns'),int) else None,scheduler_gap_ms=(newer.get('slot_begin_ns')-older.get('present_record_done_ns'))/1e6 if isinstance(newer.get('slot_begin_ns'),int) and isinstance(older.get('present_record_done_ns'),int) else None,refresh=newer.get('refresh'),source_older=newer.get('source_older'),display_index=newer.get('display_index'),alpha=newer.get('alpha'),deadline_lateness_ms=(newer['present_begin_ns']-newer['presentation_deadline_ns'])/1e6 if isinstance(newer.get('presentation_deadline_ns'),int) else None,present_call_ms=(present_end-newer['present_begin_ns'])/1e6 if isinstance(present_end,int) else None,cpu_call_ms=newer.get('cpu_call_ns',0)/1e6,pose_sample_ms=newer.get('pose_sample_cpu_ns',0)/1e6,draw_ms=newer.get('draw_cpu_ns',0)/1e6,pacing_wait_ms=newer.get('pacing_wait_ns',0)/1e6,source_queue_age_ms=(dequeued-submitted)/1e6 if isinstance(dequeued,int) and isinstance(submitted,int) else None,pair_prepare_ms=newer.get('pair_prepare_ns',0)/1e6,full_scene=bool(newer.get('full_scene_sampled')),sky=bool(newer.get('sky_interpolated'))))
  worst_gaps=sorted(gaps,key=lambda x:x['interval_ms'],reverse=True)[:10]
  pair_alphas={}
  for row in shown:
   pair=(row.get('source_older'),row.get('refresh'));alpha=row.get('alpha')
   if all(isinstance(x,int) for x in pair) and isinstance(alpha,(int,float)):
    pair_alphas.setdefault(pair,[]).append(float(alpha))
  pair_sizes=[len(values) for values in pair_alphas.values()]
  pair_summary=dict(source_pairs=len(pair_sizes),pairs_with_multiple_presentations=sum(n>1 for n in pair_sizes),median_presentations_per_pair=statistics.median(pair_sizes) if pair_sizes else None,max_presentations_per_pair=max(pair_sizes) if pair_sizes else None,alpha_values_changed_within_pair=sum(len({round(v,6) for v in values})>1 for values in pair_alphas.values()),alpha_nonmonotonic_steps=sum(b+1e-6<a for values in pair_alphas.values() for a,b in zip(values,values[1:])))
  sky_pair_phases={}
  for row in shown:
   pair=(row.get('sky_source_older'),row.get('sky_source_newer'));alpha=row.get('sky_slot_alpha');phase=row.get('sky_phase');old_angle=row.get('sky_angle_older');new_angle=row.get('sky_angle_newer')
   if row.get('sky_interpolated') and all(isinstance(x,int) for x in pair) and isinstance(alpha,(int,float)) and isinstance(phase,(int,float)) and isinstance(old_angle,int) and isinstance(new_angle,int):
    delta=((new_angle-old_angle+8192)&16383)-8192
    sky_pair_phases.setdefault(pair,[]).append((float(alpha),float(phase),delta))
  sky_pair_sizes=[len(values) for values in sky_pair_phases.values()]
  sky_phase_steps=[]
  for values in sky_pair_phases.values():
   ordered=sorted(values,key=lambda x:x[0]);direction=ordered[0][2] if ordered else 0
   for before,after in zip(ordered,ordered[1:]):
    step=(after[1]-before[1]+120)%240-120
    if direction and abs(step)>1e-6:sky_phase_steps.append(dict(direction=direction,step=step))
  sky_pair_summary=dict(source_pairs=len(sky_pair_sizes),pairs_with_multiple_presentations=sum(n>1 for n in sky_pair_sizes),median_presentations_per_pair=statistics.median(sky_pair_sizes) if sky_pair_sizes else None,max_presentations_per_pair=max(sky_pair_sizes) if sky_pair_sizes else None,phase_values_changed_within_pair=sum(len({round(item[1],6) for item in values})>1 for values in sky_pair_phases.values()),phase_nonmonotonic_steps=sum((item['step']<0 if item['direction']>0 else item['step']>0) for item in sky_phase_steps))
  return dict(original_updates=updates,live_seconds=live_ns/1e9,original_updates_per_second=updates/(live_ns/1e9) if live_ns else None,scene_submissions=scene_submissions,presented_samples=len(shown),full_scene_samples=sum(bool(r.get('full_scene_sampled')) for r in shown),sky_samples=sum(bool(r.get('sky_interpolated')) for r in shown),presentation_interval=metrics(intervals),deadline_lateness=metrics(lateness[1:]),present_call=metrics(present_calls),producer_queue_space_wait=metrics(waits),source_pair_interpolation=pair_summary,sky_pair_interpolation=sky_pair_summary,worst_presentation_gaps=worst_gaps,formal_60fps_verified=False)
 progress('arguments_parsed')
 if not 0<=opt.diagnostic_sky_wraps<=4 or (opt.diagnostic_sky_wraps and not (opt.interpolate_sky and opt.smoke_seconds)):raise ValueError("Sky capture requires timed sky interpolation and limit0..4")
 if opt.smoke_steering and not opt.smoke_seconds:raise ValueError("Scripted steering requires timed diagnostic run")
 assert not opt.show_smoke_window or opt.smoke_seconds>0
 if opt.profile_preparation_refresh is not None:assert opt.background_prepare and opt.smoke_seconds and opt.profile_preparation_refresh>=0
 assert not opt.shared_process_output or opt.process_prepare
 if opt.process_prepare:assert opt.full_scene and opt.background_prepare and opt.precompute_world_samples and opt.profile_preparation_refresh is None
 model_pose_trace=None
 model_scene_captures=[];model_scene_dir=None;sky_inplace_checks=[]
 if opt.diagnostic_model_scenes:
  assert 1<=opt.diagnostic_model_scenes<=16 and opt.smoke_seconds and opt.model_scene_step>=1
  opt.graph_snapshots=True
  model_scene_dir=Path('work/camera/prototype-runs')/('model-scenes-'+str(time.time_ns()));model_scene_dir.mkdir(parents=True)
 original_thread_switch=sys.getswitchinterval()
 if opt.python_thread_switch_ms is not None:
  assert .5<=opt.python_thread_switch_ms<=5;assert opt.background_prepare
  sys.setswitchinterval(opt.python_thread_switch_ms/1000)
 if opt.presentation_delay_refreshes is not None:assert opt.interpolate or opt.full_scene;assert 4<=opt.presentation_delay_refreshes<=18
 if opt.diagnostic_scene_thresholds:
  assert opt.smoke_seconds and len(opt.diagnostic_scene_thresholds)<=16 and sorted(set(opt.diagnostic_scene_thresholds))==opt.diagnostic_scene_thresholds
  opt.diagnostic_wall_frames=len(opt.diagnostic_scene_thresholds);
 if opt.diagnostic_wall_frames:assert (opt.regenerate_walls or opt.full_scene) and opt.smoke_seconds and 0<opt.diagnostic_wall_frames<=16
 if opt.regenerate_walls:opt.graph_snapshots=True
 if opt.smoke_initial_pause:assert opt.smoke_seconds>=2 and not opt.smoke_pause and not opt.smoke_repeat_pause and not opt.smoke_quit_paused
 if opt.smoke_pause:assert opt.smoke_seconds>=2
 if opt.smoke_quit_paused:assert opt.smoke_seconds>=2 and not opt.smoke_pause and not opt.smoke_repeat_pause
 if opt.smoke_repeat_pause:assert opt.smoke_seconds>=25 and not opt.smoke_pause
 if opt.full_scene:opt.interpolate=True;opt.graph_snapshots=True
 if opt.gpu_finish:assert opt.interpolate
 setup=Path('work/camera/capture_motion_scanline_state.py').read_text().split('gpu=None;gpu_worker=None;gpu_checks=[]')[0]
 if opt.smoke_state!='work/race.state':
  state_path=Path(opt.smoke_state).resolve();work_root=Path('work').resolve()
  if not state_path.is_file() or not state_path.is_relative_to(work_root):raise ValueError('Alternate smoke state must be an existing file inside the project work directory')
  state_token="state=p.parent/'race.state'"
  if state_token not in setup:raise ValueError('Capture setup no longer contains the expected protected race-state binding')
  setup=setup.replace(state_token,f'state=Path({str(state_path)!r})',1)
 if opt.continuous_sky and not opt.interpolate_sky:raise ValueError("Continuous sky requires --interpolate-sky")
 if (opt.interpolate_sky or opt.attach_sky) and not (opt.capture_sky and opt.full_scene):raise ValueError("Sky interpolation requires full-scene sky capture")
 if opt.native_sky_inplace and not (opt.interpolate_sky and opt.capture_sky and opt.full_scene and opt.graph_snapshots and opt.smoke_seconds):raise ValueError('In-place sky candidate requires bounded full-scene sky smoke')
 if opt.audio_device_position and not opt.experimental_audio:raise ValueError('Device position diagnostic requires experimental audio')
 if opt.experimental_audio and not opt.capture_sky:raise ValueError('Original audio requires isolated sky bridge')
 if opt.capture_sky:
  assert opt.full_scene,'Sky capture requires complete scene ownership'
  setup=setup.replace('visibility-probe-wide.dll','sky-caller-probe.dll')
 if opt.capture_probe_candidate:
  if not opt.capture_sky:raise ValueError('Viewport probe requires sky capture')
  setup=setup.replace('sky-caller-probe.dll',opt.capture_probe_candidate)
 progress('capture_setup_begin')
 exec(compile(setup,'capture_setup','exec'))
 progress('capture_setup_complete')
 for k in list(os.environ):
  if k.startswith('NF_') and k!='NF_TEST_RACING_OWNED_CAPTURE':os.environ.pop(k,None);assert crt._putenv((k+'=').encode())==0
 if opt.thread_native_frame_join:
  assert opt.full_scene and opt.background_prepare and not opt.process_prepare
  import owned_sampled_world_frame as frame_assembly
  from owned_native_frame_join import join_frame,trace,helper
  helper()
  frame_assembly.join_frame=join_frame;frame_assembly.join_frame_trace=trace
 if opt.process_native_frame_join:
  assert opt.process_prepare
  os.environ['NF_PROCESS_NATIVE_FRAME_JOIN']='1'
 if opt.shared_output_dedup:os.environ['NF_SHARED_DEDUP_BYTES']='1'
 if opt.native_road_reader:os.environ['NF_NATIVE_ROAD_READER']='1'
 if opt.preparation_process_below_normal:
  assert opt.process_prepare
  os.environ["NF_PREPARATION_BELOW_NORMAL"]="1"
 assert not (opt.direct_capture_ram and opt.bus_capture_ram)
 assert not (opt.direct_capture_rom and opt.bus_capture_rom)
 assert not (opt.verify_capture_rom and opt.bus_capture_rom)
 if not opt.bus_capture_rom:
  os.environ['NF_TEST_DIRECT_CAPTURE_ROM']='1';assert crt._putenv(b'NF_TEST_DIRECT_CAPTURE_ROM=1')==0
 if opt.verify_capture_rom:
  os.environ['NF_TEST_VERIFY_CAPTURE_ROM']='1';assert crt._putenv(b'NF_TEST_VERIFY_CAPTURE_ROM=1')==0
 if not opt.bus_capture_ram:
  os.environ['NF_TEST_DIRECT_CAPTURE_RAM']='1';assert crt._putenv(b'NF_TEST_DIRECT_CAPTURE_RAM=1')==0
 if opt.capture_sky:
  os.environ['NF_CAPTURE_INDEXED_COPY']='1';assert crt._putenv(b'NF_CAPTURE_INDEXED_COPY=1')==0
 assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0)
 assert d.nf_native_scene_sink(text_scene_sink,None)
 rom_owned=rom.read_bytes();assert d.nf_live_visibility_enable(rom_owned,len(rom_owned),16*1024*1024);assert d.nf_bitmap_text_enable(1)
 d.nf_native_live_latest_frame.restype=C.c_uint;d.nf_native_live_scene_count.restype=C.c_uint
 from owned_sky_capture import SkyCapture
 sky_capture=SkyCapture(d,rom.read_bytes()) if opt.capture_sky else None
 from owned_gc_trace import CollectionTrace
 gc_trace=CollectionTrace() if opt.gc_trace else None
 worker=LiveOwnedGPUWorker(d.nf_native_scene_epoch(),sky_renderer_candidate=opt.sky_renderer_candidate,gpu_query_only=opt.gpu_query_only,native_commit_stages=opt.native_commit_stages,draw_only=True,present=True,paced=True,verify=False,delay_refreshes=opt.presentation_delay_refreshes if opt.presentation_delay_refreshes is not None else 6 if opt.interpolate else 4,expected_frames=None,show_window=not opt.smoke_seconds or opt.show_smoke_window,interpolate=opt.interpolate,diagnostic_finish=opt.gpu_finish,diagnostic_async_timer=opt.gpu_async_timer,full_scene_rom=rom_owned if opt.full_scene else None,background_prepare=opt.background_prepare,precompute_world_samples=opt.precompute_world_samples,process_prepare=opt.process_prepare,shared_process_output=opt.shared_process_output,swap_interval=opt.swap_interval,renderer_thread_priority=opt.renderer_thread_priority,native_present_callback=opt.native_present_callback,sky_continuous=opt.continuous_sky,sky_interpolate=opt.interpolate_sky,diagnostic_sky_wraps=opt.diagnostic_sky_wraps,boundary_cpu=opt.boundary_cpu,native_notification_queue=opt.native_notification_queue)
 if opt.batch_gpu_timestamps:
  assert type(worker).__name__=='NativeBatchWorker'
  worker.gpu_timestamp_probe_enabled=True
 if opt.batch_gpu_fences:
  assert type(worker).__name__=='NativeBatchWorker'
  worker.gpu_fence_probe_enabled=True
 if opt.present_completion_barrier:assert type(worker).__name__ in ("NativeTransactionWorker","NativeBatchWorker")
 worker.present_completion_barrier=opt.present_completion_barrier
 if opt.preparation_cache_range is not None:
  assert worker.preparation_service is not None and opt.preparation_cache_range[0]<=opt.preparation_cache_range[1]
  worker.preparation_service.cache_diagnostic_range=tuple(opt.preparation_cache_range)
 if opt.profile_preparation_refresh is not None:worker.preparation_service.profile_refresh=opt.profile_preparation_refresh
 wall_failure=None
 sky_identity_skips=dict(count=0,examples=[])
 wall_diagnostics=[];wall_diagnostic_dir=None
 if opt.diagnostic_wall_frames:
  wall_diagnostic_dir=Path('work/camera/prototype-runs')/('wall-diagnostic-'+str(time.time_ns()));wall_diagnostic_dir.mkdir(parents=True)
 producer_costs=[];simulation_costs=[]
 wall_checks=[];wall_reciprocal=None
 if opt.regenerate_walls:
  import struct
  wall_reciprocal=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072])
 graph_checks=[]
 d.nf_owned_graph_closed_read.argtypes=[C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
 d.nf_owned_model_builders_closed_read.argtypes=[C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
 d.nf_owned_supplement_closed_read.argtypes=[C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
 frame=C.create_string_buffer(0x1000000);last=0;submitted=0;inputs=[];startup_inputs=[];physical_controller_samples=[];live_begin=None;last_scene_step=0;error=None
 # One immutable scene closes on the original page flip; never interpolate screen polygons.
 capture_boundary_library=None;capture_batch_checks=[]
 if opt.verify_native_capture_batch:assert opt.native_capture_batch and opt.smoke_seconds
 if opt.native_capture_boundary or opt.native_capture_batch:
  assert opt.producer_cycles
  capture_boundary_library=C.CDLL(str(Path('work/camera/owned-original-update-boundary.dll').resolve()))
  capture_boundary_library.nf_original_frame_read_boundary.argtypes=[C.c_void_p,C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p]
  capture_boundary_library.nf_original_frame_read_batch.argtypes=capture_boundary_library.nf_original_frame_read_boundary.argtypes
 def submit_latest():
  global last,submitted,last_scene_step,wall_failure
  candidate=d.nf_native_live_latest_frame()
  if candidate<=last or candidate>d.nf_layer_queue_latest():return
  if sky_capture is not None:
   # A state load can leave one startup candidate without a completed sky
   # owner. Drop only that presentation candidate; preserve exact matching.
   identity=(C.c_uint32*3)()
   if not d.nf_live_completed_sky_publication_identity(d.nf_native_scene_epoch(),candidate,identity):
    sky_identity_skips['count']+=1
    if len(sky_identity_skips['examples'])<32:
     stats=(C.c_uint32*4)();d.nf_native_scene_stats(stats)
     sky_identity_skips['examples'].append(dict(candidate=candidate,native_refresh=d.nf_native_scene_refresh(),scene_stats=list(stats)))
    last=candidate
    return
  producer_begin=time.perf_counter_ns();producer_cycle_begin=thread_cycles() if getattr(opt,'producer_cycles',False) else None;stage_times={};stage_begin=producer_begin
  size=C.c_size_t();frame_read_boundaries=[]
  def read_owned(buffer,capacity):
   if globals().get("capture_boundary_library") is None:return d.nf_native_owned_frame_read(d.nf_native_scene_epoch(),candidate,buffer,capacity,C.byref(size))
   epoch=d.nf_native_scene_epoch();boundary=(C.c_uint64*4)();started=time.perf_counter_ns()
   result=capture_boundary_library.nf_original_frame_read_boundary(C.cast(d.nf_native_owned_frame_read,C.c_void_p),epoch,candidate,buffer,capacity,C.byref(size),boundary)
   completed=time.perf_counter_ns()
   frame_read_boundaries.append(dict(query=buffer is None,started_ns=started,completed_ns=completed,native=list(boundary),success=bool(result),bytes=size.value))
   return result
  if getattr(opt,"native_capture_batch",False):
   epoch=d.nf_native_scene_epoch();boundary=(C.c_uint64*4)();started=time.perf_counter_ns()
   result=capture_boundary_library.nf_original_frame_read_batch(C.cast(d.nf_native_owned_frame_read,C.c_void_p),epoch,candidate,frame,len(frame),C.byref(size),boundary)
   frame_read_boundaries.append(dict(batch=True,query=False,started_ns=started,completed_ns=time.perf_counter_ns(),native=list(boundary),success=bool(result),bytes=size.value))
   if not result:raise RuntimeError(f"Batched complete scene read failed {candidate}")
  else:
   if not read_owned(None,0):raise RuntimeError(f"Incomplete or unavailable native source scene {candidate}")
   if not read_owned(frame,len(frame)):raise RuntimeError(f"Native scene {candidate} failed complete-frame validation")
  owned_bytes_begin=time.perf_counter_ns()
  # The closed-graph matcher accepts a read-only buffer view. Avoid creating a
  # second full-frame bytes copy on the live producer path; materialize only
  # where a diagnostic artifact or wall adapter must retain/concatenate bytes.
  owned_frame=memoryview(frame).cast('B')[:size.value] if opt.graph_snapshots or opt.regenerate_walls else None
  if owned_frame is not None and (opt.regenerate_walls or model_scene_dir is not None or wall_diagnostic_dir is not None):owned_frame=bytes(owned_frame)
  owned_bytes_end=time.perf_counter_ns()
  if getattr(opt,"verify_native_capture_batch",False) and len(capture_batch_checks)<16:
   epoch=d.nf_native_scene_epoch();legacy_size=C.c_size_t()
   assert d.nf_native_owned_frame_read(epoch,candidate,None,0,C.byref(legacy_size)) and legacy_size.value==size.value
   legacy=C.create_string_buffer(size.value)
   assert d.nf_native_owned_frame_read(epoch,candidate,legacy,len(legacy),C.byref(legacy_size))
   assert C.string_at(legacy,size.value)==C.string_at(frame,size.value),'Batched complete frame differs'
   sentinel=C.create_string_buffer(b'unchanged',9);bad_size=C.c_size_t();bad=(C.c_uint64*4)()
   assert not capture_boundary_library.nf_original_frame_read_batch(C.cast(d.nf_native_owned_frame_read,C.c_void_p),epoch,candidate,sentinel,9,C.byref(bad_size),bad)
   assert sentinel.raw==b'unchanged' and bad_size.value==size.value
   assert not capture_boundary_library.nf_original_frame_read_batch(C.cast(d.nf_native_owned_frame_read,C.c_void_p),epoch+1,candidate,sentinel,9,C.byref(bad_size),bad)
   assert sentinel.raw==b'unchanged'
   capture_batch_checks.append(dict(epoch=epoch,refresh=candidate,bytes=size.value,exact_full_frame=True,undersized_atomic=True,wrong_epoch_rejected=True))
  stage_times['frame_read_ns']=time.perf_counter_ns()-stage_begin;stage_begin=time.perf_counter_ns()
  if opt.graph_snapshots:
   from owned_closed_graph import ClosedGraph
   gn=C.c_size_t();epoch=d.nf_native_scene_epoch()
   if not d.nf_owned_graph_closed_read(epoch,candidate,None,0,C.byref(gn)):raise RuntimeError('Missing closed graph for rendered scene')
   snapshot=C.create_string_buffer(gn.value)
   if not d.nf_owned_graph_closed_read(epoch,candidate,snapshot,gn.value,C.byref(gn)):raise RuntimeError('Closed graph read failed')
   stage_times['graph_read_ns']=time.perf_counter_ns()-stage_begin;stage_begin=time.perf_counter_ns()
   graph=ClosedGraph.decode(snapshot.raw);graph.match_frame(owned_frame)
   from owned_closed_viewport import ClosedViewport
   viewport=ClosedViewport.capture(d,graph) if hasattr(d,'nf_owned_graph_closed_viewport') else None
   if viewport is not None:graph=viewport.bind_graph(graph)
   stage_times['graph_decode_match_ns']=time.perf_counter_ns()-stage_begin;stage_begin=time.perf_counter_ns()
   from owned_closed_supplements import ClosedSupplements
   sn=C.c_size_t()
   if not d.nf_owned_supplement_closed_read(epoch,candidate,None,0,C.byref(sn)):raise RuntimeError('Missing paired supplemental snapshot')
   supplement_snapshot=C.create_string_buffer(sn.value)
   if not d.nf_owned_supplement_closed_read(epoch,candidate,supplement_snapshot,sn.value,C.byref(sn)):raise RuntimeError('Paired supplemental read failed')
   stage_times['supplement_read_ns']=time.perf_counter_ns()-stage_begin;stage_begin=time.perf_counter_ns()
   supplements=ClosedSupplements.decode(supplement_snapshot.raw,graph,rom_owned)
   stage_times['supplement_decode_ns']=time.perf_counter_ns()-stage_begin;stage_begin=time.perf_counter_ns()
   from owned_model_builder_inputs import OwnedModelBuilders
   bn=C.c_size_t()
   if not d.nf_owned_model_builders_closed_read(epoch,candidate,None,0,C.byref(bn)):raise RuntimeError(f'Missing scene-owned builder inputs: refresh={candidate} epoch={epoch} status={d.nf_owned_model_builder_status()}')
   builder_snapshot=C.create_string_buffer(max(1,bn.value))
   if not d.nf_owned_model_builders_closed_read(epoch,candidate,builder_snapshot,bn.value,C.byref(bn)):raise RuntimeError('Scene-owned builder read failed')
   builders=OwnedModelBuilders(builder_snapshot.raw[:bn.value])
   if any(v.refresh>candidate for values in builders.records.values() for v in values):raise RuntimeError('Future scenery builder inputs')
   if d.nf_owned_model_builders_closed_read(epoch+1,candidate,None,0,C.byref(C.c_size_t())):raise RuntimeError('Builder epoch guard failed')
   current_api=d.nf_owned_current_sources_closed_read;current_api.argtypes=[C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
   cn=C.c_size_t();assert current_api(epoch,candidate,None,0,C.byref(cn))
   current_sources=C.create_string_buffer(cn.value);assert current_api(epoch,candidate,current_sources,cn.value,C.byref(cn))
   ch=struct.unpack_from('<6IQ',current_sources.raw)
   assert ch[:3]==(0x31534f4e,4,candidate) and ch[3]==graph.graph.refresh and ch[5]==216 and ch[6]==epoch and len(current_sources)==32+ch[4]*216
   assert not current_api(epoch+1,candidate,None,0,C.byref(C.c_size_t()))
   graph_checks.append(dict(owned_viewport=viewport is not None,viewport_address=None if viewport is None else viewport.address,refresh=candidate,builder_bytes=bn.value,bytes=gn.value,descriptors=len(graph.graph.validate()),supplemental_bytes=sn.value,supplemental_geometry_bytes=len(supplements.geometry),supplemental_texture_bytes=len(supplements.textures)))
  if model_scene_dir and len(model_scene_captures)<opt.diagnostic_model_scenes and candidate>=opt.model_scene_min_refresh and (not model_scene_captures or candidate-model_scene_captures[-1]['refresh']>=opt.model_scene_step):
   paths={}
   for extension,payload in (('frame',owned_frame),('graph',snapshot.raw),('supplements',supplement_snapshot.raw),('builders',builder_snapshot.raw[:bn.value]),('current-sources',current_sources.raw)):
    path=model_scene_dir/(str(candidate)+'.'+extension+'.bin');path.write_bytes(payload);paths[extension]=str(path)
   if viewport is not None:
    path=model_scene_dir/(str(candidate)+'.viewport.bin');path.write_bytes(viewport.encode());paths['viewport']=str(path)
   model_scene_captures.append(dict(refresh=candidate,**paths))
  if opt.regenerate_walls:
   from owned_live_wall_adapter import reconstruct
   original_frame=owned_frame;began=time.perf_counter_ns()
   try:adapted,walls=reconstruct(owned_frame,graph,supplements,wall_reciprocal)
   except ValueError as exc:
    if wall_diagnostic_dir:
     prefix=wall_diagnostic_dir/(str(candidate)+'-failure')
     paths=dict(frame=str(prefix.with_suffix('.frame.bin')),graph=str(prefix.with_suffix('.graph.bin')),supplements=str(prefix.with_suffix('.supplements.bin')))
     Path(paths['frame']).write_bytes(original_frame);Path(paths['graph']).write_bytes(snapshot.raw);Path(paths['supplements']).write_bytes(supplement_snapshot.raw)
     if viewport is not None:
      paths['viewport']=str(prefix.with_suffix('.viewport.bin'));Path(paths['viewport']).write_bytes(viewport.encode())
     wall_failure=dict(refresh=candidate,error=str(exc),**paths)
    raise
   reconstruction_ns=time.perf_counter_ns()-began
   if len(adapted)>len(frame):raise RuntimeError('Reconstructed scene exceeds frame capacity')
   C.memmove(frame,adapted,len(adapted));size.value=len(adapted);wall_checks.append(dict(refresh=candidate,walls=walls,reconstruction_ns=reconstruction_ns))
  if not opt.regenerate_walls:original_frame=owned_frame;adapted=owned_frame
  if wall_diagnostic_dir and len(wall_diagnostics)<opt.diagnostic_wall_frames and (not opt.diagnostic_scene_thresholds or candidate>=opt.diagnostic_scene_thresholds[len(wall_diagnostics)]):
   original_path=wall_diagnostic_dir/(str(candidate)+'-original.bin');adapted_path=wall_diagnostic_dir/(str(candidate)+'-regenerated.bin')
   publication=None
   if opt.capture_sky:
    ident=(C.c_uint32*3)();detail=(C.c_uint32*8)();d.nf_live_completed_sky_publication_identity.argtypes=[C.c_uint64,C.c_uint,C.c_void_p];d.nf_live_completed_capture_detail.argtypes=[C.c_uint64,C.c_uint,C.c_void_p]
    assert d.nf_live_completed_sky_publication_identity(d.nf_native_scene_epoch(),candidate,ident) and d.nf_live_completed_capture_detail(d.nf_native_scene_epoch(),ident[0],detail)
    assert ident[2]+1==candidate and detail[7]<=1
    publication=dict(serial=int(ident[0]),begin=int(ident[1]),end=int(ident[2]),page=int(detail[7]),capture_detail=list(detail))
   pixel_path=wall_diagnostic_dir/(str(candidate)+'-original-video.rgba');pixel_address=d.nf_pixels();assert pixel_address;pixel_path.write_bytes(C.string_at(pixel_address,240*160*4))
   original_path.write_bytes(original_frame);adapted_path.write_bytes(adapted);graph_path=wall_diagnostic_dir/(str(candidate)+'-graph.bin');supplements_path=wall_diagnostic_dir/(str(candidate)+'-supplements.bin');graph_path.write_bytes(snapshot.raw);supplements_path.write_bytes(supplement_snapshot.raw);wall_diagnostics.append(dict(viewport=None if viewport is None else str(wall_diagnostic_dir/(str(candidate)+'-viewport.bin')),refresh=candidate,publication=publication,original_video=str(pixel_path),original_video_refresh=d.nf_native_scene_refresh(),input_count=len(startup_inputs)+len(inputs),requested_threshold=opt.diagnostic_scene_thresholds[len(wall_diagnostics)] if opt.diagnostic_scene_thresholds else None,original=str(original_path),regenerated=str(adapted_path),graph=str(graph_path),supplements=str(supplements_path)))
  scene=None
  if opt.graph_snapshots and viewport is not None and wall_diagnostics and wall_diagnostics[-1]['refresh']==candidate:
   (wall_diagnostic_dir/(str(candidate)+'-viewport.bin')).write_bytes(viewport.encode())
  if opt.graph_snapshots:
   from owned_motion_scene import MotionScene
   scene=MotionScene(graph,supplements,builders,__import__('owned_model_sources').OwnedModelSources.decode(current_sources.raw,graph),sky_capture.read(graph) if sky_capture is not None else None,viewport)
  stage_times['reconstruction_and_scene_ns']=time.perf_counter_ns()-stage_begin;stage_begin=time.perf_counter_ns()
  if opt.interpolate_sky or opt.attach_sky:
   if opt.native_sky_inplace:
    from owned_sky_frame import attach_sky_inplace
    if not sky_inplace_checks:
     from owned_sky_frame import attach_sky
     expected_sky=attach_sky(C.string_at(frame,size.value),scene)
     attach_sky_inplace(frame,scene,size.value)
     actual_sky=C.string_at(frame,size.value)
     if actual_sky!=expected_sky:raise RuntimeError('In-place sky attachment differs from immutable reference')
     sky_inplace_checks.append(dict(refresh=candidate,bytes=size.value,byte_exact=True))
    else:
     attach_sky_inplace(frame,scene,size.value)
    sky_frame=frame
   else:
    from owned_sky_frame import attach_sky
    sky_frame=attach_sky(C.string_at(frame,size.value),scene)
  stage_times['sky_attachment_ns']=time.perf_counter_ns()-stage_begin;stage_begin=time.perf_counter_ns()
  worker.submit(sky_frame if (opt.interpolate_sky or opt.attach_sky) else frame,size.value,scene=scene);stage_times['worker_submit_ns']=time.perf_counter_ns()-stage_begin;last=candidate;submitted+=1;last_scene_step=len(inputs)
  if live_begin is not None:producer_costs.append(dict(refresh=candidate,started_ns=producer_begin,completed_ns=time.perf_counter_ns(),thread_cycles=thread_cycles()-producer_cycle_begin if producer_cycle_begin is not None else None,ns=time.perf_counter_ns()-producer_begin,stages=stage_times,frame_read_boundaries=frame_read_boundaries,owned_bytes_copy=dict(started_ns=owned_bytes_begin,completed_ns=owned_bytes_end)))
 from owned_smoke_pause_schedule import SmokePauseSchedule
 smoke_pause_schedule=SmokePauseSchedule((0,) if opt.smoke_initial_pause else (1,10,20) if opt.smoke_repeat_pause else (1,) if opt.smoke_pause else ())
 def controls():
  if opt.smoke_seconds:
   elapsed=(time.perf_counter_ns()-live_begin)/1e9
   scripted=dict(keys=(1|(32 if 80<=len(inputs)<400 else 16 if 400<=len(inputs)<600 else 0)) if opt.smoke_steering else 1,paused=(elapsed>=opt.smoke_seconds-1 if opt.smoke_quit_paused else (smoke_pause_schedule.paused(elapsed) if not opt.smoke_initial_pause or getattr(worker,'initial_pause_gate_waiting',False) else False)),quit=elapsed>=opt.smoke_seconds)
   if opt.smoke_physical_controller:
    live=worker.controls()
    physical_controller_samples.append(dict(elapsed_seconds=round(elapsed,3),keys=live['keys'],paused=live['paused'],quit=live['quit'],connected=live['controller_connected']))
    if live['controller_connected']:
     return dict(keys=live['keys'],paused=live['paused'],quit=live['quit'] or scripted['quit'],controller_connected=True)
    scripted['paused']=scripted['paused'] or live['paused'];scripted['quit']=scripted['quit'] or live['quit'];scripted['controller_connected']=False
   return scripted
  return worker.controls()
 audio=None;audio_events=[];audio_base=None;audio_shutdown=None
 original_update_samples=[];update_timer=None;update_boundary=None
 # Synchronous calls retain their function owner and reuse scratch storage.
 original_frame_callback=d.nf_frame
 original_frame_address=C.c_void_p.from_buffer(original_frame_callback).value
 boundary=(C.c_uint64*5)();native=(C.c_uint64*2)();profile=(C.c_uint64*6)()
 if opt.capture_update_profile:
  assert opt.producer_cycles and opt.original_update_boundary
  d.nf_capture_profile_enable(1)
  d.nf_capture_profile_read.argtypes=[C.c_void_p]
 if opt.original_update_boundary:
  update_boundary=C.CDLL(str(Path("work/camera/owned-original-update-boundary.dll").resolve()))
  update_boundary.nf_original_update_boundary_cpu.argtypes=[C.c_void_p,C.c_uint,C.c_void_p]
 if opt.gpu_async_timer:
  update_timer=C.CDLL(str(Path('work/camera/owned-original-update-timer.dll').resolve()))
  update_timer.nf_original_update_timed.argtypes=[C.c_void_p,C.c_uint,C.c_void_p]
 def audio_controls():
  state=controls()
  if audio is not None and state['paused'] and not audio.paused:
   audio.retire();audio_events.append(dict(event='retire',refresh=d.nf_native_scene_refresh(),generation=audio.generation))
  return state
 def advance(keys):
  global audio_base
  if audio is not None and audio.paused:
   if not audio.resume():raise RuntimeError('Audio flush acknowledgement not ready on resume')
   audio_base=d.nf_native_scene_refresh()
   audio_events.append(dict(event='resume',refresh=audio_base,generation=audio.generation))
  refresh=d.nf_native_scene_refresh();inputs.append(dict(refresh=refresh,keys=keys,control_snapshot=dict(gate.last_state),control_snapshot_ns=gate.last_state_ns));began=time.perf_counter_ns();update_cycle_begin=thread_cycles() if getattr(opt,'producer_cycles',False) else None
  native_boundary=None
  if update_boundary is not None:
   assert update_boundary.nf_original_update_boundary_cpu(original_frame_address,keys,boundary)
   native_boundary=list(boundary)
  elif update_timer is None:original_frame_callback(keys)
  else:
   assert update_timer.nf_original_update_timed(original_frame_address,keys,native)
   original_update_samples.append(dict(refresh=refresh,native_elapsed_ns=int(native[0]),native_thread_cpu_ns=int(native[1]) if native[1]!=2**64-1 else None))
  if opt.producer_cycles:original_update_samples.append(dict(refresh=refresh,started_ns=began,completed_ns=time.perf_counter_ns(),thread_cycles=thread_cycles()-update_cycle_begin,native_boundary=native_boundary,original_deadline_ns=gate.last_deadline_ns,clock_origin=gate.last_clock_origin,clock_base=gate.last_clock_base))
  if opt.capture_update_profile:
   assert d.nf_capture_profile_read(profile)
   original_update_samples[-1]["capture_profile"]=list(profile)
  simulation_costs.append(time.perf_counter_ns()-began)
  if audio is not None:
   # The reset-local sample stream starts at this original refresh offset.
   ticks=(audio_base-worker.clock_base)*280896
   origin=worker.clock_origin+(ticks*1000000000+16777215)//16777216
   if not audio.pump_retry_busy(refresh,origin,worker.delay_refreshes):
    # Stop visibly instead of dropping sound or altering simulation timing.
    raise RuntimeError('Experimental audio backpressure: retained PCM; live run stopped')
   state=audio.status();position=(C.c_uint64*8)();submission=(C.c_uint64*8)()
   assert audio.output.nf_audio_output_last_submission(audio.handle,submission)
   valid=audio.output.nf_audio_output_position(audio.handle,audio.epoch,audio.generation,position)
   audio_events.append(dict(event='admit',refresh=refresh,clock_origin=origin,status=state,position=list(position) if valid else None,submission=list(submission)))
 try:
  # Saved-state override arms scene ownership before advancing, so startup rows
  # from the protected race.state ledger are never replayed against another state.
  started=False
  trace_just_armed=False
  if opt.smoke_state=='work/race.state':
   for row in rows:
    if d.nf_native_scene_refresh()>=8749 and not started:
     assert d.nf_world_trace(b'') and d.nf_layer_queue_enable(1)
     if opt.graph_snapshots:assert d.nf_owned_graph_live_enable(1)
     assert d.nf_native_model_plan_trace(b'',model_plan_table,len(model_plan_table));started=True;trace_just_armed=True
     if opt.diagnostic_model_poses:
      model_pose_trace=Path('work/camera/prototype-runs')/('model-poses-'+str(time.time_ns())+'.bin');model_pose_trace.parent.mkdir(parents=True,exist_ok=True)
      d.nf_owned_object_pose_trace.argtypes=[C.c_char_p];assert d.nf_owned_object_pose_trace(str(model_pose_trace).encode())
      d.nf_owned_model_builder_trace.argtypes=[C.c_char_p];assert d.nf_owned_model_builder_trace(str(model_pose_trace.with_suffix('.builders.bin')).encode())
      d.nf_owned_slot_trace.argtypes=[C.c_char_p];assert d.nf_owned_slot_trace(str(model_pose_trace.with_suffix('.slots.bin')).encode())
      d.nf_watch.argtypes=[C.c_uint,C.c_uint];d.nf_watch(33577012+136,1)
      d.nf_owned_model_outcome_trace.argtypes=[C.c_char_p];assert d.nf_owned_model_outcome_trace(str(model_pose_trace.with_suffix('.outcomes.bin')).encode())
    startup_inputs.append(dict(refresh=d.nf_native_scene_refresh(),keys=int(row['keys'])))
    d.nf_frame(int(row['keys']))
    if trace_just_armed:
     # The first page publication can still reference source records from
     # before trace arming. Treat it as an incomplete capture, not a scene.
     last=d.nf_native_live_latest_frame();trace_just_armed=False
    elif started:submit_latest()
    if submitted:break
  else:
   if not opt.full_scene or not opt.capture_sky or not opt.graph_snapshots:raise ValueError('Alternate-state capture requires full-scene source/sky/graph capture')
   assert d.nf_world_trace(b'') and d.nf_layer_queue_enable(1) and d.nf_owned_graph_live_enable(1)
   assert d.nf_native_model_plan_trace(b'',model_plan_table,len(model_plan_table));started=True
   for index in range(720):
    keys=1|(32 if 180<=index<300 else 16 if 500<=index<720 else 0)
    startup_inputs.append(dict(refresh=d.nf_native_scene_refresh(),keys=keys))
    d.nf_frame(keys)
    candidate=d.nf_native_live_latest_frame()
    if candidate>last and candidate<=d.nf_layer_queue_latest() and d.nf_owned_graph_closed_latest()==candidate:
     submit_latest()
     if submitted:break
   if not submitted:raise RuntimeError('Alternate saved state did not produce a complete source-owned scene within 720 updates')
  progress('first_frame_wait_begin',submitted=submitted)
  if not submitted:raise RuntimeError('No complete initial scene was submitted')
  if not worker.first_frame_ready.wait(30):
   progress('first_frame_wait_timeout',submitted=submitted,worker_errors=list(worker.errors))
   raise TimeoutError('Renderer did not acknowledge its first source frame within 30 seconds')
  if worker.errors:raise RuntimeError(f'GPU worker failed before first frame: {worker.errors!r}')
  progress('first_frame_ready',worker_errors=len(worker.errors))
  startup_readiness=None
  if opt.startup_readiness:
   if not opt.background_prepare:raise ValueError('Startup readiness requires background preparation')
   first_frame,first_scene=worker.preparation_previous
   before_refresh=d.nf_native_scene_refresh();started_ready=time.perf_counter_ns()
   progress('startup_readiness_begin',refresh=int(first_scene.identity[1]));startup_readiness=worker.preparation_service.warm_start(first_frame,first_scene);progress('startup_readiness_complete',refresh=int(first_scene.identity[1]))
   startup_readiness['wait_wall_ns']=time.perf_counter_ns()-started_ready
   startup_readiness['simulation_refresh']=before_refresh
   assert before_refresh==d.nf_native_scene_refresh()
   assert startup_readiness['refresh']==first_scene.identity[1]
  if opt.experimental_audio:
   from owned_audio_stream import OwnedAudioStream
   output=C.CDLL(str(Path('work/camera/owned-audio-output.dll').resolve()))
   output.nf_audio_output_last_submission.argtypes=[C.c_void_p,C.c_void_p]
   output.nf_audio_output_position.argtypes=[C.c_void_p,C.c_uint64,C.c_uint64,C.c_void_p]
   audio=OwnedAudioStream(d,output,d.nf_native_scene_epoch(),minimum_frames=2048)
   deadline=time.monotonic()+5
   while not audio.status()[3]:
    if time.monotonic()>deadline:raise RuntimeError('Audio device startup timeout')
    time.sleep(.002)
   output.nf_audio_output_position_enable.argtypes=[C.c_void_p,C.c_int]
   if opt.audio_device_position:assert output.nf_audio_output_position_enable(audio.handle,1)
   audio_base=d.nf_native_scene_refresh()
  progress('live_clock_start_begin',refresh=int(d.nf_native_scene_refresh()))
  live_begin=time.perf_counter_ns();worker.start_clock(live_begin,d.nf_native_scene_refresh())
  progress('live_clock_started',refresh=int(d.nf_native_scene_refresh()))
  producer_wait_samples=[]
  if opt.native_producer_wait:
   wait_library=C.CDLL(str(Path('work/camera/owned-original-update-boundary.dll').resolve()))
   wait_library.nf_original_deadline_wait_slice.argtypes=[C.c_uint64,C.c_void_p]
   original_wait=worker.wait_until
   def producer_wait(deadline,pause_revision=None):
    if threading.get_ident()!=worker.producer:return original_wait(deadline,pause_revision)
    while True:
     if pause_revision is not None and (worker.paused or worker.pause_revision!=pause_revision):return False
     if deadline<=time.perf_counter_ns():return True
     sample=(C.c_uint64*3)();assert wait_library.nf_original_deadline_wait_slice(deadline,sample)
     if len(producer_wait_samples)<10000:producer_wait_samples.append(dict(deadline_ns=deadline,started_ns=int(sample[0]),completed_ns=int(sample[1]),fallback=bool(sample[2])))
   worker.wait_until=producer_wait
  gate=LiveGameControls(worker,advance,d.nf_native_scene_refresh,snapshot=audio_controls)
  while gate.step():
   submit_latest()
   if len(inputs)-last_scene_step>120:raise RuntimeError('Native scene source stalled; this game state is unsupported.')
 except BaseException as e:
  error=repr(e);raise
 finally:
  live_observation_stats=worker.results.stats() if hasattr(worker.results,'stats') else None
  live_observation_end_ns=time.perf_counter_ns()
  live_elapsed_ns=live_observation_end_ns-live_begin if live_begin is not None else None
  progress('worker_close_begin')
  try:worker.close();progress('worker_close_complete');progress('compact_run_summary',summary=compact_run_summary(worker.results,worker.submit_stage_samples,len(inputs),submitted,live_elapsed_ns or 0,live_begin or 0))
  except BaseException as close_error:
   error=error or repr(close_error);raise
  finally:
   if audio is not None:
    try:
     audio_shutdown=dict(status=audio.status(),accepted=audio.accepted,retries=audio.retries,last_result=audio.last_result,pending=dict(frames=audio.pending[1],refresh=audio.pending[2],deadline=audio.pending[3],sha256=hashlib.sha256(C.string_at(audio.pending[0],audio.pending[1]*4)).hexdigest()) if audio.pending else None)
     audio.close();audio_shutdown['closed']=True
    except BaseException as audio_error:
     audio_shutdown=dict(closed=False,error=repr(audio_error));error=error or repr(audio_error)
   if gc_trace is not None:gc_trace.close()
   sys.setswitchinterval(original_thread_switch)
   logs=p/'prototype-runs';logs.mkdir(exist_ok=True);out=logs/('owned-native-'+str(time.time_ns())+'.json')
   final_ram={};final_ram_error=None
   for name,address,n in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
    try:
     target=out.with_suffix('.'+name+'.bin');d.nf_dump(str(target).encode(),address,n)
     if target.stat().st_size!=n:raise OSError('Incomplete final RAM snapshot')
     final_ram[name]=dict(path=str(target),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),bytes=n)
    except BaseException as dump_error:
     final_ram_error=f'{name}: {dump_error!r}';error=error or final_ram_error;break
   rom_copy_counters=(C.c_uint64*3)();d.nf_capture_rom_copy_stats.argtypes=[C.c_void_p];d.nf_capture_rom_copy_stats(rom_copy_counters)
   hook_diagnostics=None
   if model_pose_trace:
    hc=(C.c_uint32*128)();hs=(C.c_uint32*3)();d.nf_owned_material_hook_counts.argtypes=[C.c_void_p];d.nf_arm_hook_status.argtypes=[C.c_void_p];d.nf_owned_material_hook_counts(hc);d.nf_arm_hook_status(hs)
    hook_diagnostics=dict(status=list(hs),material_counts={hex(0x03002300+i*4):n for i,n in enumerate(hc) if n})
    d.nf_hist.argtypes=[C.c_char_p];d.nf_hist(str(model_pose_trace.with_suffix('.slot-writers.csv')).encode())
   d.nf_owned_slot_trace.argtypes=[C.c_char_p];d.nf_owned_slot_trace(None);d.nf_owned_model_builder_trace(None);d.nf_owned_model_outcome_trace(None);d.nf_owned_object_pose_trace(None);d.nf_owned_graph_live_enable(0);d.nf_native_model_plan_trace(None,None,0);d.nf_world_trace(None);d.nf_close()
   assert all(hashlib.sha256(Path(x).read_bytes()).hexdigest()==v for x,v in protected.items())
   import statistics
   def cost_summary(values):
    return dict(count=len(values),total_ms=sum(values)/1e6,median_ms=statistics.median(values)/1e6 if values else None,max_ms=max(values)/1e6 if values else None)
   timing=dict(live_elapsed_ns=live_elapsed_ns,original_clock_hz=16777216,cycles_per_update=280896,simulated_seconds=len(inputs)*280896/16777216,wall_seconds=live_elapsed_ns/1e9 if live_elapsed_ns is not None else None,simulation_with_source_hooks=cost_summary(simulation_costs),producer_read_validate_reconstruct_submit=cost_summary([row['ns'] for row in producer_costs]),producer_stages={key:cost_summary([row['stages'].get(key,0) for row in producer_costs]) for key in sorted({key for row in producer_costs for key in row['stages']})},scope='Live CPU stage wall durations; simulation includes native capture hooks, producer excludes GPU worker. Wall interval includes pauses. No steady-state60fps certification.')
   report=dict(live_observation_stats=live_observation_stats,live_observation_begin_ns=live_begin,live_observation_end_ns=live_observation_end_ns,live_observation_scope="Producer gameplay loop before worker close; consumer may finish pending work afterward. Pause durations included, active display starts after configured delay.",thread_native_frame_join_enabled=opt.thread_native_frame_join,native_capture_batch_enabled=opt.native_capture_batch,native_sky_inplace_enabled=opt.native_sky_inplace,sky_inplace_checks=sky_inplace_checks,capture_batch_checks=capture_batch_checks,native_producer_wait_enabled=opt.native_producer_wait,producer_wait_samples=locals().get("producer_wait_samples",[]),producer_cycles_enabled=opt.producer_cycles,producer_cycle_samples=producer_costs,sky_renderer_candidate=opt.sky_renderer_candidate,gpu_query_only_enabled=opt.gpu_query_only,preparation_queue_samples=getattr(getattr(worker.preparation_service,"pipeline",None),"timings",[]),boundary_cpu_enabled=opt.boundary_cpu,audio_device_position_enabled=opt.audio_device_position,experimental_audio_enabled=opt.experimental_audio,audio_events=audio_events,audio_shutdown=audio_shutdown,audio_video_sync_verified=False,sky_endpoint_attachment_enabled=bool(opt.attach_sky or opt.interpolate_sky),sky_wrap_captures=worker.sky_wrap_captures,smoke_steering_enabled=opt.smoke_steering,sky_continuous_enabled=opt.continuous_sky,sky_interpolation_enabled=opt.interpolate_sky,sky_capture_records=sky_capture.records if sky_capture is not None else [],sky_capture_enabled=opt.capture_sky,sky_identity_startup_skips=sky_identity_skips,startup_readiness=locals().get('startup_readiness'),renderer_priority_evidence=getattr(worker,'priority_evidence',None),quit_while_paused=worker.paused,shutdown_evidence=getattr(worker,'shutdown_evidence',None),window_shown=worker.show_window,swap_interval_requested=opt.swap_interval,swap_interval_observed=worker.swap_interval_observed,shared_process_output_enabled=opt.shared_process_output,rom_copy_stats=list(rom_copy_counters),direct_capture_rom_enabled=not opt.bus_capture_rom,verify_capture_rom_enabled=opt.verify_capture_rom,direct_capture_ram_enabled=not opt.bus_capture_ram,original_update_samples=original_update_samples,consumer_boundary_stage_samples=worker.boundary_stage_samples,process_preparation_enabled=opt.process_prepare,gc_collection_samples=gc_trace.rows if gc_trace else [],gc_trace_dropped=gc_trace.dropped if gc_trace else 0,producer_thread_id=threading.get_ident(),preparation_cache_diagnostics=getattr(worker.preparation_service,'cache_diagnostics',[]),live_preparation_profiles=getattr(worker.preparation_service,'profiles',[]),slow_hud_capture_manifest=getattr(worker,"slow_hud_capture_manifest",None),compact_presentation_diagnostic_stats=getattr(worker,"compact_presentation_diagnostic_stats",None),compact_preparation_diagnostic_stats=getattr(worker.preparation_service,"compact_diagnostic_stats",None),world_preparation_stage_samples=getattr(worker.preparation_service,'stage_samples',[]),worker_submit_stage_samples=getattr(worker,'submit_stage_samples',[]),hook_diagnostics=hook_diagnostics,model_scene_captures=model_scene_captures,model_pose_trace=str(model_pose_trace) if model_pose_trace else None,world_samples_precomputed=opt.precompute_world_samples,python_thread_switch_ms=opt.python_thread_switch_ms,presentation_delay_refreshes=worker.delay_refreshes,background_preparation_enabled=opt.background_prepare,full_scene_failure_capture=worker.world_failure_capture,full_scene_history_resets=worker.world_resets,full_scene_sampling_enabled=opt.full_scene,wall_failure=wall_failure,timing=timing,wall_diagnostic_frames=wall_diagnostics,regenerated_wall_validation=wall_checks,graph_snapshot_validation=graph_checks,result='FAILED' if error else 'SMOKE_COMPLETE' if opt.smoke_seconds else 'INTERACTIVE_CLOSED',error=error,original_updates=len(inputs),owned_scene_submissions=submitted,presentations=len(worker.results),interpolation_enabled=opt.interpolate,diagnostic_gpu_finish=opt.gpu_finish,diagnostic_gpu_async_timer=opt.gpu_async_timer,gpu_timer_skipped=worker.gpu_timer_skipped,gpu_timer_pending=worker.pending_gpu_timer,presentation_samples=worker.results if opt.interpolate else [],native_batch_timing_trace=getattr(worker,'batch_timing_trace',[]),native_batch_method_calls=getattr(worker,'batch_method_calls',0),inputs=inputs,startup_inputs=startup_inputs,final_ram=final_ram,final_ram_error=final_ram_error,pause_events=worker.pause_events,smoke_scripted_inputs=bool(opt.smoke_seconds),physical_controller_telemetry=dict(enabled=opt.smoke_physical_controller,samples=len(physical_controller_samples),connected_samples=sum(bool(x['connected']) for x in physical_controller_samples),nonzero_key_samples=sum(bool(x['keys']) for x in physical_controller_samples),paused_samples=sum(bool(x['paused']) for x in physical_controller_samples),trace=physical_controller_samples),smooth_60fps_verified=False,physical_controller_verified=False,scope='Continuous original-cycle game loop with complete source scenes and endpoint presentation. Startup recorded; experimental audio optional and synchronization unverified; optional pose interpolation remains unverified for full-scene fidelity; game states outside source capture may stop.')
   report['input_state_path']=str(state);report['input_state_sha256']=protected[str(state)];report['input_state_loaded_read_only']=True
   progress('report_write_begin',updates=len(inputs),submissions=submitted,presentations=len(worker.results))
   out.write_text(json.dumps(report,indent=2));progress('report_write_complete',report=str(out));print(out);print({k:report[k] for k in ('result','original_updates','owned_scene_submissions','presentations')})
 
 
 
 
 
 
