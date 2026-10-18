"""Experimental full-scene native draw/wait/commit worker; default unchanged."""
import ctypes as C,time,struct,threading
from concurrent.futures import CancelledError
from live_owned_gpu_worker import LiveOwnedGPUWorker
from owned_motion_clock import scene_samples
P=C.c_void_p;U=C.c_uint64;Callback=C.CFUNCTYPE(C.c_int,P)
class DrawContext(C.Structure):
 _fields_=[('frame',P),('bytes',C.c_size_t),('camera',P),('models',P),('bounds',P),('count',C.c_uint),('lower',P),('upper',P),('skycount',C.c_size_t),('weight',C.c_double),('result',C.c_int),('started_ns',U),('completed_ns',U),('thread_cycles',U)]
class PresentContext(C.Structure):_fields_=[('epoch',U),('timed',C.c_uint32),('result',C.c_int32),('elapsed_ns',U)]
class NativeTransactionWorker(LiveOwnedGPUWorker):
 def _draw_intervals(self,gpu,previous,current,generation,refresh,epoch,submitted_ns,dequeued_ns,scene):
  assert self.full_scene_rom is not None and self.preparation_service is not None and self.sky_interpolate and self.sky_continuous and self.native_present_callback
  assert not self.diagnostic_async_timer and not self.diagnostic_finish and not self.gpu_query_only and self.sky_renderer_candidate is None
  self.d.nf_owned_handoff_commit_token.argtypes=[P,U,U,Callback,P]
  wait_revision=self.pause_revision
  pair_begin=time.perf_counter_ns();owned_scene_pair=previous[3] is not None and scene is not None;pair=None if self.full_scene_rom is not None else PreparedMotionPair(previous[0],current,previous[3] if owned_scene_pair else None,scene if owned_scene_pair else None)
  if self.full_scene_rom is not None:
   if not owned_scene_pair:raise ValueError('Fullscene live mode requires complete paired snapshots')
   from owned_endpoint_road_planner import EndpointRoadPlanner
   from owned_prepared_world_motion import PreparedWorldMotion
   if self.preparation_service is not None:
    claimed=[]
    def claim_future(ctx):
     with self.scene_snapshot_lock:claimed.append(self.preparation_futures.pop((previous[3].identity,scene.identity),None))
     return 1
    claim_callback=Callback(claim_future)
    valid=self.d.nf_owned_handoff_commit_token(self.owner,epoch,generation,claim_callback,None)
    if valid==0:return False
    assert valid==1 and len(claimed)==1
    future=claimed[0]
    if future is None:
     # Pause may retire this popped token and clear its future before Python
     # observes the pause revision. Ask the native lifecycle authority.
     token_probe=Callback(lambda ctx:1)
     valid=self.d.nf_owned_handoff_commit_token(self.owner,epoch,generation,token_probe,None)
     if valid==0:return False
     assert valid==1
     raise ValueError('Missing owned background interval')
    try:pair=self.world_pair=self.preparation_service.take(future)
    except CancelledError:
     token_probe=Callback(lambda ctx:1)
     valid=self.d.nf_owned_handoff_commit_token(self.owner,epoch,generation,token_probe,None)
     if valid==0:return False
     assert valid==1
     raise
   else:
    if self.world_history is None:
     table=struct.unpack('<32768I',(self.p/'road-correction-reciprocal.bin').read_bytes()[:131072]);self.world_history=EndpointRoadPlanner(self.full_scene_rom,table)
     self.world_roads,_=self.world_history.plan(previous[3].graph)
    pair=self.world_pair=PreparedWorldMotion(previous[0],current,previous[3],scene,self.world_history,self.world_roads,self.full_scene_rom)
    self.world_roads,_=self.world_history.plan(scene.graph)
  pair_ready_ns=time.perf_counter_ns();pair_prepare_ns=pair_ready_ns-pair_begin
  bridge=C.CDLL(str(self.p/'owned-draw-commit-candidate.dll'))
  transaction=bridge.nf_owned_handoff_draw_wait_commit_sample
  transaction.argtypes=[P,U,U,U,U,U,C.c_double,U,Callback,P,Callback,P,P,P,P]
  draw_callback=C.cast(gpu.nf_owned_gpu_draw_context_callback,Callback);present_callback=C.cast(gpu.nf_owned_gpu_present_callback,Callback)
  gpu.nf_owned_gpu_draw_context_size.restype=C.c_size_t;assert gpu.nf_owned_gpu_draw_context_size()==C.sizeof(DrawContext)
  gpu.nf_owned_gpu_present_stages.argtypes=[P]
  completion_enabled=bool(getattr(self,"present_completion_barrier",False))
  gpu.nf_owned_gpu_present_completion_read.argtypes=[P]
  assert gpu.nf_owned_gpu_present_completion_mode(int(completion_enabled))==0
  for slot in scene_samples(self.clock_origin,self.clock_base,previous[2],refresh,self.delay_refreshes):
   if slot['index']<=self.resume_cutoff:continue
   begin=time.perf_counter_ns()
   frame,cam,models,bounds,detail=pair.sample(slot['alpha'])
   old=previous[3].sky;new=scene.sky
   if old is None or new is None or old.asset is None:raise ValueError('Missing paired sky')
   sky=old.asset.sample_continuous(old.boundary,new.boundary,slot['alpha'])
   # All pointer owners remain strongly held until the native transaction returns.
   fb=C.create_string_buffer(frame);lo=C.create_string_buffer(sky.lower);hi=C.create_string_buffer(sky.upper)
   ctx=DrawContext(C.cast(fb,P),len(frame),C.cast(cam,P),C.cast(models,P),C.cast(bounds,P),detail['geometry_records'],C.cast(lo,P),C.cast(hi,P),15136,sky.weight,-999,0,0,0)
   pc=PresentContext(epoch,1,-999,0);sample=(U*8)();wait=(U*4)();stages=(U*7)();present_stages=(U*3)()
   with self.presentation_publication_lock:
    called=time.perf_counter_ns()
    result=transaction(self.owner,epoch,generation,previous[2],refresh,slot['index'],slot['alpha'],slot['deadline_ns'],draw_callback,C.byref(ctx),present_callback,C.byref(pc),sample,wait,stages)
    returned=time.perf_counter_ns();assert result in (0,1),(result,ctx.result,pc.result)
    if not result:return False
    assert ctx.result==pc.result==0 and gpu.nf_owned_gpu_present_stages(present_stages)==0
    completion=(U*3)();assert gpu.nf_owned_gpu_present_completion_read(completion)==0
    self.results.append(dict(present_completion_barrier=completion_enabled,present_completion_boundary=list(completion),native_transaction_candidate=True,consumer_thread=threading.get_ident(),context_count=self.context_counter(),epoch=epoch,generation=generation,refresh=refresh,source_older=previous[2],display_index=slot['index'],alpha=slot['alpha'],interpolated=True,hidden_window_presented=True,full_scene_sampled=True,complete_scene_pair_retained=True,sky_interpolated=True,sky_phase_mode='continuous_angle',sky_fraction=sky.weight,native_committed_sample=list(sample),native_commit_stage_ns=list(stages),native_wait_timing=list(wait),presentation_deadline_ns=slot['deadline_ns'],present_begin_ns=stages[0],present_end_ns=returned,commit_return_ns=returned,native_present_stage_ns=list(present_stages),sample_begin_ns=begin,draw_complete_ns=ctx.completed_ns,draw_cpu_ns=ctx.completed_ns-ctx.started_ns,native_draw_boundary=[ctx.started_ns,ctx.completed_ns,ctx.thread_cycles,0],transaction_begin_ns=called,transaction_return_ns=returned,pair_begin_ns=pair_begin,pair_ready_ns=pair_ready_ns,pair_prepare_ns=pair_prepare_ns,source_submitted_ns=submitted_ns,source_dequeued_ns=dequeued_ns,surface_detail=detail,native_present_callback=True,input_draw_batched=True))
  return True
