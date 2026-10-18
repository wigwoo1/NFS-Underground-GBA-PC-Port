"""Experimental source-owned native endpoint gameplay host; no 60fps interpolation yet."""
from pathlib import Path
import ctypes as C,time,json,hashlib,sys,argparse
from live_owned_gpu_worker import LiveOwnedGPUWorker
from live_game_controls import LiveGameControls
args=argparse.ArgumentParser();args.add_argument('--smoke-seconds',type=float,default=0);args.add_argument('--diagnostic-wall-frames',type=int,default=0);args.add_argument('--regenerate-walls',action='store_true');args.add_argument('--graph-snapshots',action='store_true');args.add_argument('--interpolate',action='store_true');args.add_argument('--smoke-pause',action='store_true');args.add_argument('--gpu-finish',action='store_true');opt=args.parse_args();assert 0<=opt.smoke_seconds<=120
if opt.diagnostic_wall_frames:assert opt.regenerate_walls and opt.smoke_seconds and 0<opt.diagnostic_wall_frames<=16
if opt.regenerate_walls:opt.graph_snapshots=True
if opt.smoke_pause:assert opt.smoke_seconds>=2
if opt.gpu_finish:assert opt.interpolate
setup=Path('work/camera/capture_motion_scanline_state.py').read_text().split('gpu=None;gpu_worker=None;gpu_checks=[]')[0]
exec(compile(setup,'capture_setup','exec'))
for k in list(os.environ):
 if k.startswith('NF_') and k!='NF_TEST_RACING_OWNED_CAPTURE':os.environ.pop(k,None);assert crt._putenv((k+'=').encode())==0
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0)
assert d.nf_native_scene_sink(text_scene_sink,None)
rom_owned=rom.read_bytes();assert d.nf_live_visibility_enable(rom_owned,len(rom_owned),16*1024*1024);assert d.nf_bitmap_text_enable(1)
d.nf_native_live_latest_frame.restype=C.c_uint;d.nf_native_live_scene_count.restype=C.c_uint
worker=LiveOwnedGPUWorker(d.nf_native_scene_epoch(),draw_only=True,present=True,paced=True,verify=False,delay_refreshes=6 if opt.interpolate else 4,expected_frames=None,show_window=not opt.smoke_seconds,interpolate=opt.interpolate,diagnostic_finish=opt.gpu_finish)
wall_diagnostics=[];wall_diagnostic_dir=None
if opt.diagnostic_wall_frames:
 wall_diagnostic_dir=Path('work/camera/prototype-runs')/('wall-diagnostic-'+str(time.time_ns()));wall_diagnostic_dir.mkdir(parents=True)
wall_checks=[];wall_reciprocal=None
if opt.regenerate_walls:
 import struct
 wall_reciprocal=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072])
graph_checks=[]
d.nf_owned_graph_closed_read.argtypes=[C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
d.nf_owned_supplement_closed_read.argtypes=[C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)]
frame=C.create_string_buffer(0x1000000);last=0;submitted=0;inputs=[];startup_inputs=[];live_begin=None;last_scene_step=0;error=None
# One immutable scene closes on the original page flip; never interpolate screen polygons.
def submit_latest():
 global last,submitted,last_scene_step
 candidate=d.nf_native_live_latest_frame()
 if candidate<=last or candidate>d.nf_layer_queue_latest():return
 size=C.c_size_t()
 if not d.nf_native_owned_frame_read(d.nf_native_scene_epoch(),candidate,None,0,C.byref(size)):raise RuntimeError(f"Incomplete or unavailable native source scene {candidate}")
 if not d.nf_native_owned_frame_read(d.nf_native_scene_epoch(),candidate,frame,len(frame),C.byref(size)):raise RuntimeError(f"Native scene {candidate} failed complete-frame validation")
 if opt.graph_snapshots:
  from owned_closed_graph import ClosedGraph
  gn=C.c_size_t();epoch=d.nf_native_scene_epoch()
  if not d.nf_owned_graph_closed_read(epoch,candidate,None,0,C.byref(gn)):raise RuntimeError('Missing closed graph for rendered scene')
  snapshot=C.create_string_buffer(gn.value)
  if not d.nf_owned_graph_closed_read(epoch,candidate,snapshot,gn.value,C.byref(gn)):raise RuntimeError('Closed graph read failed')
  graph=ClosedGraph.decode(snapshot.raw);graph.match_frame(frame.raw[:size.value])
  from owned_closed_supplements import ClosedSupplements
  sn=C.c_size_t()
  if not d.nf_owned_supplement_closed_read(epoch,candidate,None,0,C.byref(sn)):raise RuntimeError('Missing paired supplemental snapshot')
  supplement_snapshot=C.create_string_buffer(sn.value)
  if not d.nf_owned_supplement_closed_read(epoch,candidate,supplement_snapshot,sn.value,C.byref(sn)):raise RuntimeError('Paired supplemental read failed')
  supplements=ClosedSupplements.decode(supplement_snapshot.raw,graph)
  graph_checks.append(dict(refresh=candidate,bytes=gn.value,descriptors=len(graph.graph.validate()),supplemental_bytes=sn.value,supplemental_geometry_bytes=len(supplements.geometry),supplemental_texture_bytes=len(supplements.textures)))
 if opt.regenerate_walls:
  from owned_live_wall_adapter import reconstruct
  original_frame=frame.raw[:size.value];began=time.perf_counter_ns()
  adapted,walls=reconstruct(frame.raw[:size.value],graph,supplements,wall_reciprocal)
  reconstruction_ns=time.perf_counter_ns()-began
  if wall_diagnostic_dir and len(wall_diagnostics)<opt.diagnostic_wall_frames:
   original_path=wall_diagnostic_dir/(str(candidate)+'-original.bin');adapted_path=wall_diagnostic_dir/(str(candidate)+'-regenerated.bin')
   original_path.write_bytes(original_frame);adapted_path.write_bytes(adapted);wall_diagnostics.append(dict(refresh=candidate,original=str(original_path),regenerated=str(adapted_path)))
  if len(adapted)>len(frame):raise RuntimeError('Reconstructed scene exceeds frame capacity')
  C.memmove(frame,adapted,len(adapted));size.value=len(adapted);wall_checks.append(dict(refresh=candidate,walls=walls,reconstruction_ns=reconstruction_ns))
 worker.submit(frame,size.value);last=candidate;submitted+=1;last_scene_step=len(inputs)
def controls():
 if opt.smoke_seconds:
  elapsed=(time.perf_counter_ns()-live_begin)/1e9
  return dict(keys=1,paused=opt.smoke_pause and 1<=elapsed<1.2,quit=elapsed>=opt.smoke_seconds)
 return worker.controls()
def advance(keys):
 inputs.append(dict(refresh=d.nf_native_scene_refresh(),keys=keys));d.nf_frame(keys)
try:
 # Retained recorded startup establishes the first complete racing scene, outside live clock.
 started=False
 for row in rows:
  if d.nf_native_scene_refresh()>=8749 and not started:
   assert d.nf_world_trace(b'') and d.nf_layer_queue_enable(1)
   if opt.graph_snapshots:assert d.nf_owned_graph_live_enable(1)
   assert d.nf_native_model_plan_trace(b'',model_plan_table,len(model_plan_table));started=True
  startup_inputs.append(dict(refresh=d.nf_native_scene_refresh(),keys=int(row['keys'])))
  d.nf_frame(int(row['keys']));submit_latest()
  if submitted:break
 assert submitted and worker.first_frame_ready.wait(30) and not worker.errors
 live_begin=time.perf_counter_ns();worker.start_clock(live_begin,d.nf_native_scene_refresh())
 gate=LiveGameControls(worker,advance,d.nf_native_scene_refresh,snapshot=controls)
 while gate.step():
  submit_latest()
  if len(inputs)-last_scene_step>120:raise RuntimeError('Native scene source stalled; this game state is unsupported.')
except BaseException as e:
 error=repr(e);raise
finally:
 try:worker.close()
 finally:
  logs=p/'prototype-runs';logs.mkdir(exist_ok=True);out=logs/('owned-native-'+str(time.time_ns())+'.json')
  final_ram={}
  for name,address,n in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000)]:
   target=out.with_suffix('.'+name+'.bin');d.nf_dump(str(target).encode(),address,n);assert target.stat().st_size==n
   final_ram[name]=dict(path=str(target),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),bytes=n)
  d.nf_owned_graph_live_enable(0);d.nf_native_model_plan_trace(None,None,0);d.nf_world_trace(None);d.nf_close()
  assert all(hashlib.sha256(Path(x).read_bytes()).hexdigest()==v for x,v in protected.items())
  report=dict(wall_diagnostic_frames=wall_diagnostics,regenerated_wall_validation=wall_checks,graph_snapshot_validation=graph_checks,result='FAILED' if error else 'SMOKE_COMPLETE' if opt.smoke_seconds else 'INTERACTIVE_CLOSED',error=error,original_updates=len(inputs),owned_scene_submissions=submitted,presentations=len(worker.results),interpolation_enabled=opt.interpolate,diagnostic_gpu_finish=opt.gpu_finish,presentation_samples=worker.results if opt.interpolate else [],inputs=inputs,startup_inputs=startup_inputs,final_ram=final_ram,pause_events=worker.pause_events,smoke_scripted_inputs=bool(opt.smoke_seconds),smooth_60fps_verified=False,physical_controller_verified=False,scope='Continuous original-cycle game loop with complete source scenes and endpoint presentation. Startup recorded; no audio, no pose interpolation; game states outside source capture may stop.')
  out.write_text(json.dumps(report,indent=2));print(out);print({k:report[k] for k in ('result','original_updates','owned_scene_submissions','presentations')})
