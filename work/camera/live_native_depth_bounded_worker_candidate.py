"""Isolated native live integration; successful visible cadence remains unverified."""
from live_owned_gpu_worker import LiveOwnedGPUWorker
from concurrent.futures import CancelledError
from pathlib import Path
import ctypes as C,threading,queue,struct,time
from owned_thread_cycles import read as thread_cycles
P=C.c_void_p;U=C.c_uint64;Callback=C.CFUNCTYPE(C.c_int,P)
class NativeLiveWorker(LiveOwnedGPUWorker):
 def controls(self):
  assert threading.get_ident()==self.producer
  if self.errors:raise RuntimeError(self.errors)
  if not self.input_ready.wait(5):raise RuntimeError('Native input unavailable')
  state=self.native_worker.input_snapshot()
  return dict(keys=state[0],paused=bool(state[1]),quit=bool(state[2]),controller_connected=bool(state[3]))
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
  from owned_motion_clock import scene_samples
  from owned_source_draw_context_candidate import OwnedSourceDraw
  old,new=previous[3].sky,scene.sky
  if old is None or new is None:raise ValueError('Missing continuous sky source')
  for slot in scene_samples(self.clock_origin,self.clock_base,previous[2],refresh,self.delay_refreshes):
   if slot['index']<=self.resume_cutoff:continue
   alpha=slot['alpha'];frame,camera,models,bounds,detail=pair.sample(alpha)
   offsets,mask,total,_=pair.source_masks[alpha]
   sky=old.asset.sample_continuous(old.boundary,new.boundary,alpha)
   owned=OwnedSourceDraw(frame,camera,models,bounds,detail['geometry_records'],*pair.source_cameras,alpha,offsets,mask,total).attach_sky(sky)
   row=self.native_commit.run(owned,epoch,generation,previous[2],refresh,slot['index'],alpha,slot['deadline_ns'])
   row.update(sky_phase_mode="continuous_angle",sky_fraction=sky.weight,source_submitted_ns=submitted_ns,source_dequeued_ns=dequeued_ns,native_d3d_candidate=True,epoch=epoch,generation=generation,refresh=refresh,source_older=previous[2],display_index=slot['index'],alpha=alpha,presentation_deadline_ns=slot['deadline_ns'],consumer_thread=threading.get_ident(),context_count=0,interpolated=True,full_scene_sampled=True,sky_interpolated=True,complete_scene_pair_retained=True,hidden_window_presented=row['native_result']==1,native_committed_sample=row['commit'] if row['native_result']==1 else None)
   self.results.append(row)
   if row['native_result']==0:return False
  return True
 def consume(self):
  gpu=None;previous=None;priority=None
  try:
   from owned_thread_priority import ThreadPriorityLease
   priority=ThreadPriorityLease(self.renderer_thread_priority)
   from owned_native_source_backdrop_batch_worker_candidate import NativeSourceWorker
   from owned_native_source_timed_commit_adapter_candidate import NativeSourceCommitAdapter
   gpu=self.native_worker=NativeSourceWorker()
   self.native_commit=NativeSourceCommitAdapter(gpu,self.owner)
   self.context_counter=lambda:0;self.context_creation_base=0
   self.input_ready.set()
   previous_frame_free_ns=None;previous_frame_free_execution=None
   while True:
    loop_started_ns=time.perf_counter_ns()
    if gpu.error:raise gpu.error
    input_ready_ns=time.perf_counter_ns()
    notification_wait_begin_ns=time.perf_counter_ns()
    notification_wait_cpu=time.thread_time_ns() if self.boundary_cpu else None
    notification_wait_cycles=thread_cycles() if self.boundary_cpu else None
    try:signal=self.signals.get(timeout=.01)
    except queue.Empty:continue
    if not signal:break
    submitted_ns=signal[0];dequeued_ns=time.perf_counter_ns();dequeued_cpu=time.thread_time_ns() if self.boundary_cpu else None
    notification_wait_cycles_end=thread_cycles() if self.boundary_cpu else None
    size=C.c_size_t();generation=C.c_uint64();popped=C.c_void_p();pop_attempts=0
    for attempt in range(4):
     pop_attempts+=1;pop_status=self.try_pop(self.owner,C.byref(popped),C.byref(size),C.byref(generation))
     if pop_status!=-2:break
     if attempt<3:time.sleep(0)
    if pop_status==-2:owner=self.d.nf_owned_handoff_pop_token(self.owner,C.byref(size),C.byref(generation))
    else:
     assert pop_status in (0,1),pop_status;owner=popped.value
    self.space.release()
    popped_ns=time.perf_counter_ns();popped_cpu=time.thread_time_ns() if self.boundary_cpu else None
    if not owner:continue
    try:
     raw=C.string_at(owner,40);refresh=struct.unpack_from('<I',raw,4)[0];epoch=struct.unpack_from('<Q',raw,24)[0];assert epoch==self.epoch
     with self.scene_snapshot_lock:owned_snapshot=self.scene_snapshots.pop((epoch,refresh),None)
     owned_frame,scene=owned_snapshot if owned_snapshot is not None else (None,None)
     snapshot_ready_ns=time.perf_counter_ns();snapshot_cpu=time.thread_time_ns() if self.boundary_cpu else None
     if scene is not None:
      if not self.frame_matches(owner,size.value,owned_frame,len(owned_frame)):raise ValueError('Native/immutable owned frame mismatch')
      current=owned_frame
     else:current=C.string_at(owner,size.value) if self.interpolate else None
     copied_ns=time.perf_counter_ns();copied_cpu=time.thread_time_ns() if self.boundary_cpu else None
     if scene is not None:scene.match(current)
     matched_ns=time.perf_counter_ns();matched_cpu=time.thread_time_ns() if self.boundary_cpu else None
     if len(self.boundary_stage_samples)<10000:self.boundary_stage_samples.append(dict(refresh=refresh,native_notification_get=getattr(self.signals,'last_get',None),source_submitted_ns=submitted_ns,notification_wait_begin_ns=notification_wait_begin_ns,notification_wait_cpu_ns=dequeued_cpu-notification_wait_cpu if self.boundary_cpu else None,notification_wait_thread_cycles=notification_wait_cycles_end-notification_wait_cycles if self.boundary_cpu else None,loop_started_ns=loop_started_ns,input_ready_ns=input_ready_ns,previous_frame_free_ns=previous_frame_free_ns,previous_frame_free_execution=previous_frame_free_execution,held_frame_free=self.held_frame_free,dequeued_ns=dequeued_ns,popped_ns=popped_ns,snapshot_ready_ns=snapshot_ready_ns,copied_ns=copied_ns,matched_ns=matched_ns,frame_bytes=size.value,immutable_frame_reused=scene is not None,try_pop_attempts=pop_attempts,try_pop_status=pop_status,copy_and_match_thread_cpu_ns=matched_cpu-snapshot_cpu if self.boundary_cpu else None,thread_cpu_stamps=[dequeued_cpu,popped_cpu,snapshot_cpu,copied_cpu,matched_cpu] if self.boundary_cpu else None))
     if self.full_scene_rom is not None and self.world_generation!=generation.value:
      self.reset_world_history('generation_changed',generation.value)
     if self.resume_seed==(epoch,refresh):
      previous=(current,generation.value,refresh,scene);self.resume_seed=None
      continue
     if self.interpolate and previous and previous[1]==generation.value and self.clock_origin is not None:
      retained=self.draw_intervals(gpu,previous,current,generation.value,refresh,epoch,submitted_ns,dequeued_ns,scene)
      previous=(current,generation.value,refresh,scene) if retained else None
      continue
     if scene is None:raise ValueError('Native startup requires complete source snapshot')
     previous=(current,generation.value,refresh,scene)
     self.startup_source_seeded=True
     self.first_frame_ready.set() # Source readiness only; no visible presentation claim.
    finally:
     free_cpu_begin=time.thread_time_ns() if self.boundary_cpu else None
     free_cycles_begin=thread_cycles() if self.boundary_cpu else None
     free_begin_ns=time.perf_counter_ns()
     self.frame_free(owner)
     previous_frame_free_ns=[free_begin_ns,time.perf_counter_ns()]
     previous_frame_free_execution=dict(thread_cpu_ns=time.thread_time_ns()-free_cpu_begin,thread_cycles=thread_cycles()-free_cycles_begin) if self.boundary_cpu else None
  except BaseException as e:self.errors.append(repr(e))
  finally:
   if priority is not None:
    try:priority.close();self.priority_evidence=priority.evidence()
    except Exception as failure:self.errors.append(repr(failure))
   self.reset_world_history('worker_shutdown')
   if gpu:
    try:gpu.close();self.active_contexts_after_close=0
    except BaseException as failure:self.errors.append(repr(failure))
 def close(self):
  if self.owner is None:return
  close_begin_ns=time.perf_counter_ns()
  open_pause=None
  if self.paused and self.pause_begin is not None:
   open_pause=dict(begin_ns=self.pause_begin,native_pause_ack_ns=self.pause_native_ack_ns,close_begin_ns=close_begin_ns,buffer_at_begin=self.pause_buffer_at_begin)
  limit=time.perf_counter()+30
  while self.thread.is_alive() and not self.errors:
   try:self.signals.put(0,timeout=.05);break
   except queue.Full:
    if time.perf_counter()>=limit:raise RuntimeError('GPU worker shutdown notification stalled')
  self.thread.join(max(0,limit-time.perf_counter()))
  if self.thread.is_alive():raise RuntimeError('GPU worker did not stop')
  if self.preparation_service is not None:self.preparation_service.close()
  if hasattr(self.signals,'close'):self.signals.close()
  self.d.nf_owned_handoff_destroy(self.owner);self.owner=None
  with self.scene_snapshot_lock:self.scene_snapshots.clear();self.resume_scene_chain.clear();self.pause_replay_plan=None
  self.shutdown_evidence=dict(preparation_service_shutdown=getattr(self.preparation_service,"shutdown_evidence",None),open_pause=open_pause,close_completed_ns=time.perf_counter_ns(),dxgi_shutdown=getattr(self,'dxgi_shutdown',None),gpu_queries_after_close=getattr(self,'gpu_queries_after_close',None),notification_queue_released=not hasattr(self.signals,'owner') or self.signals.owner is None,gpu_fences_after_close=getattr(self,'gpu_fences_after_close',None),active_contexts_after_close=getattr(self,'active_contexts_after_close',None),context_creation_base=getattr(self,'context_creation_base',None),gpu_thread_alive=self.thread.is_alive(),native_owner_released=self.owner is None,retained_scene_count=len(self.resume_scene_chain.items),pending_scene_count=len(self.scene_snapshots),preparation_thread_alive=self.preparation_service.pipeline.thread.is_alive() if self.preparation_service is not None and hasattr(self.preparation_service,'pipeline') else None,prepared_result_count=len(self.preparation_service.pipeline.ready) if self.preparation_service is not None and hasattr(self.preparation_service,'pipeline') else None)
  if self.errors:raise RuntimeError(self.errors)
  assert self.expected_frames is None or self.results.total_records==self.expected_frames
  self.bounded_diagnostic_stats=self.results.stats()



