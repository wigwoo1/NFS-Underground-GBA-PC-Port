"""Diagnostic live immutable-frame bridge; GPU context lives on consumer thread."""
from pathlib import Path
from concurrent.futures import CancelledError
import ctypes as C,threading,queue,struct,hashlib,time,os
from owned_thread_cycles import read as thread_cycles
class LiveOwnedGPUWorker:
 def __init__(self,epoch,draw_only=False,present=False,paced=False,verify=True,delay_refreshes=24,expected_frames=7,show_window=False,interpolate=False,diagnostic_finish=False,full_scene_rom=None,background_prepare=False,precompute_world_samples=False,diagnostic_async_timer=False,process_prepare=False,shared_process_output=False,swap_interval=None,renderer_thread_priority=0,native_present_callback=False,sky_interpolate=False,diagnostic_sky_wraps=0,boundary_cpu=False,native_commit_stages=False,sky_continuous=False,gpu_query_only=False,sky_renderer_candidate=None,native_notification_queue=False):
  if sky_renderer_candidate not in (None,'owned-sky-gpu-pingpong.dll'):raise ValueError('Unsupported sky renderer candidate')
  if sky_renderer_candidate is not None and not sky_interpolate:raise ValueError('Sky renderer candidate requires sky interpolation')
  self.sky_renderer_candidate=sky_renderer_candidate
  assert renderer_thread_priority in (0,1)
  self.gpu_query_only=bool(gpu_query_only)
  if gpu_query_only:assert interpolate and native_present_callback and not diagnostic_async_timer and not diagnostic_finish
  self.native_commit_stages_enabled=bool(native_commit_stages)
  self.native_present_callback=bool(native_present_callback)
  self.renderer_thread_priority=renderer_thread_priority;self.priority_evidence=None
  assert not shared_process_output or process_prepare
  assert swap_interval in (None,0,1)
  self.swap_interval=swap_interval;self.swap_interval_observed=None
  self.precompute_world_samples=precompute_world_samples
  if precompute_world_samples:assert background_prepare
  self.sky_wrap_limit=diagnostic_sky_wraps;self.sky_wrap_captures=[];self.sky_wrap_seen=set()
  self.sky_continuous=sky_continuous
  if sky_continuous and not sky_interpolate:raise ValueError("Continuous sky requires sky interpolation")
  self.sky_interpolate=sky_interpolate;self.full_scene_rom=full_scene_rom;self.world_history=None;self.world_roads=None;self.world_pair=None;self.world_generation=None;self.world_resets=[];self.world_failure_capture=None
  if full_scene_rom is not None:assert interpolate
  assert not (diagnostic_finish and diagnostic_async_timer)
  if diagnostic_async_timer:assert interpolate
  self.diagnostic_async_timer=diagnostic_async_timer;self.pending_gpu_timer=None;self.gpu_timer_skipped=0
  self.diagnostic_finish=diagnostic_finish
  self.interpolate=interpolate
  if interpolate:assert draw_only and present and paced and not verify and expected_frames is None
  self.show_window=show_window;self.input_ready=threading.Event();self.input_gpu=None
  self.pause_prepared=False
  self.presentation_publication_lock=threading.Lock()
  self.resume_seed=None;self.resume_cutoff=-1
  self.pause_revision=0;self.paused=False;self.pause_begin=None;self.pause_events=[];self.expected_frames=expected_frames;self.verify=verify;self.paced=paced;self.clock_origin=None;self.clock_base=0;self.delay_refreshes=delay_refreshes;self.draw_only=draw_only;self.present=present;self.p=Path('work/camera').resolve();self.d=C.CDLL(str(self.p/getattr(type(self),'handoff_library_name','owned-frame-handoff.dll')));P=C.c_void_p;Z=C.c_size_t
  self.d.nf_owned_handoff_last_sample.argtypes=[P,P]
  self.d.nf_owned_handoff_wait_token.argtypes=[P,C.c_uint64,C.c_uint64,C.c_uint64,P]
  self.try_pop=C.PYFUNCTYPE(C.c_int,P,P,P,P)(C.cast(self.d.nf_owned_handoff_try_pop_token,P).value)
  self.frame_matches=C.PYFUNCTYPE(C.c_int,P,Z,P,Z)(C.cast(self.d.nf_owned_frame_matches,P).value)
  for name,args,result in [('create',[C.c_uint64],P),('push',[P,P,Z],C.c_int),('pop',[P,P],P),('destroy',[P],None)]:
   f=getattr(self.d,'nf_owned_handoff_'+name);f.argtypes=args;f.restype=result
  self.d.nf_owned_handoff_pop_token.argtypes=[P,P,P];self.d.nf_owned_handoff_pop_token.restype=P;self.d.nf_owned_frame_free.argtypes=[P];self.d.nf_owned_handoff_create_capacity.argtypes=[C.c_uint64,C.c_uint];self.d.nf_owned_handoff_create_capacity.restype=P;self.capacity=min(8,max(3,(delay_refreshes+2)//3+2)) if paced else 3;self.owner=self.d.nf_owned_handoff_create_capacity(epoch,self.capacity);assert self.owner
  self.handoff_push=self.d.nf_owned_handoff_push_stages
  self.handoff_push.argtypes=[P,P,Z,P]
  self.frame_free=self.d.nf_owned_frame_free
  self.frame_free.restype=None
  self.held_frame_free=bool(getattr(type(self),'held_frame_free_enabled',False))
  if self.held_frame_free:self.frame_free=C.PYFUNCTYPE(None,P)(C.cast(self.d.nf_owned_frame_free,P).value)
  self.preparation_service=None;self.preparation_previous=None;self.preparation_futures={}
  if background_prepare:
   from owned_world_preparation_service import WorldPreparationService
   if process_prepare:
    assert precompute_world_samples
    from owned_process_preparation_service import ProcessPreparationService
    WorldPreparationService=ProcessPreparationService
   assert full_scene_rom is not None;self.preparation_service=WorldPreparationService(full_scene_rom,self.capacity+2,**({"shared_output":shared_process_output} if process_prepare else {}))
  from owned_resume_scene_chain import ResumeSceneChain
  self.resume_scene_chain=ResumeSceneChain(self.capacity+3)
  self.boundary_cpu=boundary_cpu;self.boundary_stage_samples=[];self.scene_snapshots={};self.scene_snapshot_lock=threading.Lock();self.signals=queue.Queue(maxsize=self.capacity) if not native_notification_queue else __import__('owned_notification_queue').NativeNotificationQueue(self.capacity);self.space=threading.Semaphore(self.capacity);self.results=getattr(type(self),"result_ledger_factory",list)();self.errors=[];self.first_frame_ready=threading.Event();self.epoch=epoch;self.producer=threading.get_ident();self.thread=threading.Thread(target=self.consume);self.thread.start()
 def poll_gpu_timer(self,gpu):
  if self.pending_gpu_timer is None:return
  elapsed=C.c_uint64();gpu.nf_owned_gpu_timer_read.argtypes=[C.POINTER(C.c_uint64)]
  status=gpu.nf_owned_gpu_timer_read(C.byref(elapsed))
  if status==38:return
  assert status==0 and elapsed.value>0,(status,elapsed.value)
  if self.pending_gpu_timer>=0:
   row=self.results[self.pending_gpu_timer]
   assert row['gpu_timer_async'],'GPU query associated with unqueried frame'
   row['gpu_elapsed_ns']=elapsed.value;row['gpu_timer_observed_ns']=time.perf_counter_ns()
  self.pending_gpu_timer=None
 def controls(self):
  """Read the renderer-published atomic snapshot on the original-game thread."""
  assert threading.get_ident()==self.producer
  if self.errors:raise RuntimeError(self.errors)
  if not self.present or not self.input_ready.wait(5):raise RuntimeError("Window input unavailable")
  state=(C.c_uint32*4)()
  assert self.input_gpu.nf_owned_input_snapshot(state)
  return dict(keys=int(state[0]),paused=bool(state[1]),quit=bool(state[2]),controller_connected=bool(state[3]))
 def start_clock(self,origin,base):
  self.clock_origin=origin;self.clock_base=base
 def wait_until(self,deadline,pause_revision=None):
  while True:
   if pause_revision is not None and (self.paused or self.pause_revision!=pause_revision):return False
   left=deadline-time.perf_counter_ns()
   if left<=0:return True
   time.sleep(min(left/1e9,.01))
 def pause_buffer_snapshot(self):
  # Copies identifiers only: diagnostic evidence never transfers ownership.
  with self.scene_snapshot_lock:
   retained=sorted(identity[1] for identity in self.resume_scene_chain.items)
   snapshots=sorted(identity[1] for identity in self.scene_snapshots)
   prepared=[dict(older=key[0][1],newer=key[1][1],done=future.done(),cancelled=future.cancelled()) for key,future in self.preparation_futures.items()]
  previous=self.preparation_previous
  committed=next((row for row in reversed(self.results) if row.get('hidden_window_presented')),None)
  native=(C.c_uint64*8)()
  if self.native_present_callback and not self.diagnostic_async_timer and not self.diagnostic_finish and self.d.nf_owned_handoff_last_sample(self.owner,native):
   alpha=struct.unpack('<d',struct.pack('<Q',native[5]))[0]
   published=dict(refresh=int(native[3]),source_older=int(native[2]),display_index=int(native[4]),alpha=alpha,generation=int(native[1]),present_end_ns=int(native[6]))
   if committed is not None and committed.get('display_index') is not None:
    assert all(published[k]==committed[k] for k in ('refresh','source_older','display_index','alpha','generation')),'Native/Python committed publication mismatch'
   committed=published

  return dict(retained_chain_refreshes=retained,snapshot_refreshes=snapshots,prepared_intervals=prepared,last_submitted_refresh=previous[1].identity[1] if previous else None,last_committed={key:committed.get(key) for key in ('refresh','source_older','display_index','alpha','generation','present_end_ns')} if committed else None,pause_revision=self.pause_revision)
 def set_paused(self,paused):
  now=time.perf_counter_ns()
  if paused==self.paused:return
  # A completed native swap must publish its index before pause chooses replay.
  with self.presentation_publication_lock:
   pause_lock_acquired_ns=time.perf_counter_ns()
   self.d.nf_owned_handoff_pause.argtypes=[C.c_void_p,C.c_uint];assert self.d.nf_owned_handoff_pause(self.owner,int(paused))
   pause_ack_ns=time.perf_counter_ns()
   buffer_snapshot=self.pause_buffer_snapshot()
  if paused:
   self.pause_native_ack_ns=pause_ack_ns
   self.pause_native_lock_wait_ns=pause_lock_acquired_ns-now
   self.pause_buffer_at_begin=buffer_snapshot;self.pause_replay_plan=None
   committed=buffer_snapshot['last_committed']
   if committed and committed.get('display_index') is not None and self.clock_origin is not None:
    with self.scene_snapshot_lock:
     self.pause_replay_plan=self.resume_scene_chain.replay_plan((self.epoch,committed['source_older']),(self.epoch,committed['refresh']),committed['display_index'],self.clock_origin,self.clock_base,self.delay_refreshes)
   elif committed and self.clock_origin is not None and committed.get('display_index') is None:
    with self.scene_snapshot_lock:
     if len(self.resume_scene_chain.items)>=2:
      first=next(iter(self.resume_scene_chain.items))
      if first!=(self.epoch,committed['refresh']):raise ValueError('Initial displayed endpoint no longer retained')
      self.pause_replay_plan=self.resume_scene_chain.initial_replay_plan(self.clock_origin,self.clock_base,self.delay_refreshes)
      self.pause_buffer_at_begin['initial_replay']=True
   if self.pause_replay_plan is not None:
    self.pause_buffer_at_begin['planned_replay_indices']=[slot['index'] for _,_,slots in self.pause_replay_plan for slot in slots]
  if self.preparation_service is not None and (paused or not self.pause_prepared):
   self.preparation_service.invalidate();self.preparation_previous=None
   with self.scene_snapshot_lock:self.preparation_futures.clear()
  self.pause_revision+=1
  self.paused=paused
  if paused:
   self.pause_begin=now;self.pause_prepared=False
   if self.preparation_service is not None and self.pause_replay_plan:
    from owned_motion_clock import scene_samples
    for old,current,pending in self.pause_replay_plan:
     alphas=tuple(x['alpha'] for x in scene_samples(self.clock_origin,self.clock_base,old[1].identity[1],current[1].identity[1],self.delay_refreshes)) if self.precompute_world_samples else None
     if self.precompute_world_samples and getattr(self.preparation_service,'supports_pending_replay',False):alphas=tuple(x['alpha'] for x in pending)
     future=self.preparation_service.submit(old,current,alphas,timeout=30,abort=lambda:bool(self.errors) or not self.thread.is_alive())
     with self.scene_snapshot_lock:self.preparation_futures[(old[1].identity,current[1].identity)]=future
    self.preparation_previous=self.pause_replay_plan[-1][1];self.pause_prepared=True
  elif self.pause_begin is not None:
   duration=now-self.pause_begin
   if self.clock_origin is not None:self.clock_origin+=duration
   self.pause_events.append(dict(begin_ns=self.pause_begin,end_ns=now,duration_ns=duration,native_pause_ack_ns=self.pause_native_ack_ns,native_resume_ack_ns=pause_ack_ns,native_pause_lock_wait_ns=self.pause_native_lock_wait_ns,native_resume_lock_wait_ns=pause_lock_acquired_ns-now,buffer_at_begin=self.pause_buffer_at_begin,buffer_at_resume=buffer_snapshot));self.pause_begin=None
   if self.pause_replay_plan:
    self.resume_cutoff=(self.pause_buffer_at_begin['planned_replay_indices'][0]-1 if self.pause_buffer_at_begin.get('initial_replay') else self.pause_buffer_at_begin['last_committed']['display_index'])
    chain=[self.pause_replay_plan[0][0]]+[b for _,b,_ in self.pause_replay_plan]
    self.resume_seed=chain[0][1].identity
    for frame,scene in chain:self.submit(frame,scene=scene,replay=True)
    self.pause_events[-1]['republished_refreshes']=[scene.identity[1] for _,scene in chain]
    self.pause_replay_plan=None
   self.pause_prepared=False
 def submit(self,frame,bytes_used=None,scene=None,replay=False):
  assert threading.get_ident()==self.producer
  # Reject reload-era input before queue reservation or preparation publication.
  used=len(frame) if bytes_used is None else bytes_used
  if used<40 or used>len(frame):raise ValueError('Invalid owned frame size')
  header=C.string_at(frame,40)
  frame_identity=(struct.unpack_from('<Q',header,24)[0],struct.unpack_from('<I',header,4)[0])
  if frame_identity[0]!=self.epoch:raise ValueError('Renderer epoch changed; recreate worker before submission')
  if scene is not None and scene.identity!=frame_identity:raise ValueError('Unpaired renderer scene identity')
  submit_begin=time.perf_counter_ns();submit_stages=dict(thread_id=threading.get_ident(),submit_begin_ns=submit_begin,scene_identity=scene.identity if scene is not None else None,replay=bool(replay),preparation_pair=None)
  limit=time.perf_counter()+30
  while True:
   if self.errors:raise RuntimeError(self.errors)
   if not self.thread.is_alive():raise RuntimeError('GPU worker stopped before submission')
   if self.space.acquire(timeout=.05):break
   if time.perf_counter()>=limit:raise RuntimeError('Renderer queue stalled')
  submit_stages['space_wait_ns']=time.perf_counter_ns()-submit_begin;stage_begin=time.perf_counter_ns()
  if self.errors:self.space.release();raise RuntimeError(self.errors)
  # Exact immutable bytes can be retained directly; mutable/native inputs still copy.
  owned_frame=(frame if type(frame) is bytes and used==len(frame) else C.string_at(frame,used)) if scene is not None else None
  submit_stages['frame_ownership_ns']=time.perf_counter_ns()-stage_begin;stage_begin=time.perf_counter_ns()
  if scene is not None:
   trace_snapshot=getattr(type(self),'snapshot_phase_trace',False)
   snapshot_enter=time.perf_counter_ns() if trace_snapshot else None
   with self.scene_snapshot_lock:
    snapshot_acquired=time.perf_counter_ns() if trace_snapshot else None
    if not replay:self.resume_scene_chain.append(owned_frame,scene)
    snapshot_appended=time.perf_counter_ns() if trace_snapshot else None
    self.scene_snapshots[scene.identity]=(owned_frame,scene)
    while len(self.scene_snapshots)>self.capacity+2:self.scene_snapshots.pop(next(iter(self.scene_snapshots)))
    snapshot_published=time.perf_counter_ns() if trace_snapshot else None
   if trace_snapshot and not replay:submit_stages['chain_append_profile']=getattr(self.resume_scene_chain,'last_append_profile',None)
   if trace_snapshot:submit_stages['snapshot_phases']=[snapshot_enter,snapshot_acquired,snapshot_appended,snapshot_published,time.perf_counter_ns()]
  submit_stages['snapshot_lock_ns']=time.perf_counter_ns()-stage_begin;stage_begin=time.perf_counter_ns()
  if self.preparation_service is not None and scene is not None and not (replay and self.pause_prepared):
   current=(owned_frame,scene)
   if self.preparation_previous is not None:
    old=self.preparation_previous;alphas=None
    submit_stages['preparation_pair']=(old[1].identity,scene.identity)
    if self.precompute_world_samples:
     from owned_motion_clock import scene_samples
     alphas=tuple(x['alpha'] for x in scene_samples(self.clock_origin or 0,self.clock_base,old[1].identity[1],scene.identity[1],self.delay_refreshes))
    try:future=self.preparation_service.submit(old,current,alphas,timeout=max(0,limit-time.perf_counter()),abort=lambda:bool(self.errors) or not self.thread.is_alive())
    except BaseException:self.space.release();raise
    with self.scene_snapshot_lock:self.preparation_futures[(old[1].identity,scene.identity)]=future
   self.preparation_previous=current
  submit_stages['preparation_submit_ns']=time.perf_counter_ns()-stage_begin;stage_begin=time.perf_counter_ns()
  # Publish paired preparation before making the native frame consumable.
  native_times=(C.c_uint64*8)()
  if not self.handoff_push(self.owner,frame,len(frame) if bytes_used is None else bytes_used,native_times):
   self.space.release();raise RuntimeError('Native scene handoff rejected')
  submit_stages['native_push_ns']=time.perf_counter_ns()-stage_begin;stage_begin=time.perf_counter_ns()
  assert native_times[6]>0
  submit_stages['native_push_timing_version']=2;submit_stages['native_push_generation']=int(native_times[7])
  for key,value in zip(('native_eligibility_wait_ns','native_eligibility_hold_ns','native_copy_unlocked_ns','native_publish_wait_ns','native_publish_hold_ns','native_push_internal_ns'),native_times[:6]):submit_stages[key]=value*1000000000//native_times[6]
  signal=(time.perf_counter_ns(),)
  submit_stages['notification_begin_ns']=signal[0]
  while True:
   if self.errors:raise RuntimeError(self.errors)
   try:self.signals.put(signal,timeout=.05);break
   except queue.Full:
    if not self.thread.is_alive():raise RuntimeError('GPU worker stopped before notification')
    if time.perf_counter()>=limit:raise RuntimeError('Renderer notification queue stalled')
  submit_stages['notification_end_ns']=time.perf_counter_ns()
  submit_stages['notification_ns']=submit_stages['notification_end_ns']-stage_begin
  submit_stages['submit_end_ns']=time.perf_counter_ns()
  if not hasattr(self,'submit_stage_samples'):self.submit_stage_samples=[]
  if len(self.submit_stage_samples)<10000:self.submit_stage_samples.append(submit_stages)
 def reset_world_history(self,reason,generation=None):
  if self.world_pair is not None:self.world_pair.close();self.world_pair=None
  if self.world_history is not None:
   self.world_resets.append(dict(reason=reason,refresh=self.world_history.refresh,generation=self.world_generation,next_generation=generation))
   self.world_history.close();self.world_history=None
  self.world_roads=None;self.world_generation=generation
 def draw_intervals(self,*args):
  try:
   retained=self._draw_intervals(*args)
   if not retained:self.reset_world_history('presentation_invalidated')
   return retained
  except Exception as failure:
   if self.full_scene_rom is not None and self.world_failure_capture is None:
    import json
    previous,current=args[1],args[2];scene=args[-1]
    folder=self.p/'prototype-runs'/('fullscene-failure-'+str(time.time_ns()));folder.mkdir()
    for label,frame,owned in (('older',previous[0],previous[3]),('newer',current,scene)):
     (folder/(label+'.frame.bin')).write_bytes(frame)
     if owned is not None:
      (folder/(label+'.graph.bin')).write_bytes(owned.graph.graph.encode())
      (folder/(label+'.objects.bin')).write_bytes(owned.graph.objects)
      if owned.builders is not None:(folder/(label+'.builders.bin')).write_bytes(owned.builders.payload)
      if owned.sources is not None:(folder/(label+'.current-sources.bin')).write_bytes(owned.sources.payload)
      (folder/(label+'.callbacks.bin')).write_bytes(owned.graph.callbacks)
      (folder/(label+'.associations.bin')).write_bytes(owned.graph.associations)
      supplements=owned.supplements
      supplemental_packet=struct.pack('<6IQ',0x3143534e,1,supplements.refresh,supplements.source_refresh,len(supplements.geometry),len(supplements.textures),supplements.epoch)+supplements.geometry+supplements.textures
      (folder/(label+'.supplements.bin')).write_bytes(supplemental_packet)
    import traceback
    self.world_failure_capture=dict(folder=str(folder),error=repr(failure),traceback=traceback.format_exc(),older=previous[2],newer=args[4],epoch=args[5])
    (folder/'failure.json').write_text(json.dumps(self.world_failure_capture,indent=2))
   raise
  finally:
   if self.world_pair is not None:self.world_pair.close();self.world_pair=None
 def _draw_intervals(self,gpu,previous,current,generation,refresh,epoch,submitted_ns,dequeued_ns,scene):
  from sample_owned_motion import PreparedMotionPair
  from owned_motion_clock import scene_samples
  gpu.nf_owned_gpu_draw_poses.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_uint]
  Callback=C.CFUNCTYPE(C.c_int,C.c_void_p)
  native_present_stages=(C.c_uint64*3)();native_present_time=C.c_uint64();native_poll_time=C.c_uint64();native_poll_stages=(C.c_uint64*4)()
  gpu.nf_owned_input_stages.argtypes=[C.c_void_p]
  gpu.nf_owned_gpu_present_stages.argtypes=[C.c_void_p]
  gpu.nf_owned_gpu_present_timed.argtypes=[C.c_uint64,C.c_void_p];gpu.nf_owned_input_poll_timed.argtypes=[C.c_void_p]
  callback_times=[None,None,None]
  def present_callback(ctx):
   callback_times[0]=time.perf_counter_ns()
   result=(gpu.nf_owned_gpu_present_timed(epoch,C.byref(native_present_time)) if self.diagnostic_async_timer else gpu.nf_owned_gpu_present(epoch))==0
   callback_times[1]=time.perf_counter_ns();return result
  native_callback_enabled=self.native_present_callback
  class PresentContext(C.Structure):
   _fields_=[('epoch',C.c_uint64),('timed',C.c_uint32),('result',C.c_int32),('elapsed_ns',C.c_uint64)]
  present_context=PresentContext(epoch,int(self.diagnostic_async_timer or self.native_commit_stages_enabled),-999,0)
  commit_context=C.byref(present_context) if native_callback_enabled else None
  commit=C.cast(gpu.nf_owned_gpu_present_callback,Callback) if native_callback_enabled else (Callback(present_callback) if self.diagnostic_async_timer else Callback(lambda ctx:gpu.nf_owned_gpu_present(epoch)==0))
  native_commit_ticks=(C.c_uint64*6)()
  self.d.nf_owned_handoff_commit_token_timed.argtypes=[C.c_void_p,C.c_uint64,C.c_uint64,Callback,C.c_void_p,C.c_void_p]
  self.d.nf_owned_handoff_commit_token.argtypes=[C.c_void_p,C.c_uint64,C.c_uint64,Callback,C.c_void_p]
  self.d.nf_owned_handoff_commit_sample.argtypes=[C.c_void_p,C.c_uint64,C.c_uint64,C.c_uint64,C.c_uint64,C.c_uint64,C.c_double,Callback,C.c_void_p,C.c_void_p]
  self.d.nf_owned_handoff_commit_sample_stages.argtypes=self.d.nf_owned_handoff_commit_sample.argtypes+[C.c_void_p]
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
    service_take_begin_ns=time.perf_counter_ns() if os.environ.get('NFSUG_CONSUMER_SERVICE_TRACE')=='1' else None
    try:pair=self.world_pair=self.preparation_service.take(future)
    except CancelledError:
     token_probe=Callback(lambda ctx:1)
     valid=self.d.nf_owned_handoff_commit_token(self.owner,epoch,generation,token_probe,None)
     if valid==0:return False
     assert valid==1
     raise
    service_take_end_ns=time.perf_counter_ns() if service_take_begin_ns is not None else None
   else:
    if self.world_history is None:
     table=struct.unpack('<32768I',(self.p/'road-correction-reciprocal.bin').read_bytes()[:131072]);self.world_history=EndpointRoadPlanner(self.full_scene_rom,table)
     self.world_roads,_=self.world_history.plan(previous[3].graph)
    pair=self.world_pair=PreparedWorldMotion(previous[0],current,previous[3],scene,self.world_history,self.world_roads,self.full_scene_rom)
    self.world_roads,_=self.world_history.plan(scene.graph)
  pair_ready_ns=time.perf_counter_ns();pair_prepare_ns=pair_ready_ns-pair_begin
  for slot in scene_samples(self.clock_origin,self.clock_base,previous[2],refresh,self.delay_refreshes):
   if slot['index']<=self.resume_cutoff:continue
   slot_begin_ns=time.perf_counter_ns()
   batched_input=self.sky_interpolate and not self.diagnostic_async_timer and not self.diagnostic_finish
   if not batched_input:assert (gpu.nf_owned_input_poll_timed(C.byref(native_poll_time)) if self.diagnostic_async_timer else gpu.nf_owned_input_poll())
   if self.diagnostic_async_timer:assert gpu.nf_owned_input_stages(native_poll_stages)
   begin=time.perf_counter_ns();surface_bounds=None;surface_detail=None
   if self.full_scene_rom is not None:frame,cm,models,surface_bounds,surface_detail=pair.sample(slot['alpha'])
   else:frame,cm,models=pair.sample(slot['alpha'])
   pose_end=time.perf_counter_ns()
   draw_cycle_begin=thread_cycles() if self.gpu_query_only else None
   draw_scope_stages=[];draw_stage_start=pose_end;draw_stage_cycles=draw_cycle_begin
   def draw_stage(name):
    nonlocal draw_stage_start,draw_stage_cycles
    if not self.gpu_query_only:return
    completed=time.perf_counter_ns();cycles=thread_cycles()
    draw_scope_stages.append(dict(name=name,started_ns=draw_stage_start,completed_ns=completed,wall_ns=completed-draw_stage_start,thread_cycles=cycles-draw_stage_cycles))
    draw_stage_start=completed;draw_stage_cycles=cycles
   async_query=False;gpu_query_begin_ns=None;gpu_query_end_ns=None
   if self.diagnostic_async_timer or self.gpu_query_only:
    self.poll_gpu_timer(gpu)
    if self.pending_gpu_timer is None:
     gpu_query_begin_ns=time.perf_counter_ns()
     assert gpu.nf_owned_gpu_timer_begin()==0;async_query=True
    else:self.gpu_timer_skipped+=1
   if self.diagnostic_finish:assert gpu.nf_owned_gpu_timer_begin()==0
   draw_stage("query_handling")
   native_draw_elapsed_ns=None;native_draw_thread_cpu_ns=None
   sky_hud_cache_stats=None
   sky_hud_stages=None
   sky_draw_stages=None
   sky_sample=None;native_draw_boundary=None
   if self.sky_interpolate:
    older_sky=previous[3].sky;newer_sky=scene.sky
    if older_sky is None or newer_sky is None or older_sky.asset is None:raise ValueError('Missing paired sky ownership')
    sky_sampler=older_sky.asset.sample_continuous if self.sky_continuous else older_sky.asset.sample
    sky_sample=sky_sampler(older_sky.boundary,newer_sky.boundary,slot['alpha'])
    if surface_bounds is None:raise ValueError('Sky requires full scene bounds')
    gpu.nf_owned_gpu_draw_scene_clips_sky.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_size_t,C.c_double]
    sky_args=(frame,len(frame),cm,models,surface_bounds,surface_detail['geometry_records'],sky_sample.lower,sky_sample.upper,15136,sky_sample.weight)
    draw_stage("sky_sample_and_arguments")
    if self.diagnostic_async_timer:
     native_times=(C.c_uint64*2)()
     gpu.nf_owned_gpu_draw_scene_clips_sky_timed.argtypes=gpu.nf_owned_gpu_draw_scene_clips_sky.argtypes+[C.c_void_p]
     sky_result=gpu.nf_owned_gpu_draw_scene_clips_sky_timed(*sky_args,native_times)
     if not sky_result:
      stages=(C.c_uint64*3)();gpu.nf_owned_gpu_sky_draw_stages.argtypes=[C.c_void_p];assert gpu.nf_owned_gpu_sky_draw_stages(stages)==0;sky_draw_stages=list(stages)
      hud_stages=(C.c_uint64*3)();gpu.nf_owned_gpu_sky_hud_stages.argtypes=[C.c_void_p];assert gpu.nf_owned_gpu_sky_hud_stages(hud_stages)==0;sky_hud_stages=list(hud_stages)
      cache_stats=(C.c_uint64*2)();gpu.nf_owned_gpu_sky_hud_cache_stats.argtypes=[C.c_void_p];assert gpu.nf_owned_gpu_sky_hud_cache_stats(cache_stats)==0;sky_hud_cache_stats=list(cache_stats)
     native_draw_elapsed_ns=int(native_times[0]);native_draw_thread_cpu_ns=int(native_times[1]) if native_times[1]!=2**64-1 else None
    else:
     if batched_input:
      gpu.nf_owned_gpu_poll_draw_scene_clips_sky.argtypes=gpu.nf_owned_gpu_draw_scene_clips_sky.argtypes
      if self.gpu_query_only and self.sky_renderer_candidate is None:
       native_draw_boundary=(C.c_uint64*4)()
       gpu.nf_owned_gpu_poll_draw_scene_clips_sky_boundary.argtypes=gpu.nf_owned_gpu_draw_scene_clips_sky.argtypes+[C.c_void_p]
       sky_result=gpu.nf_owned_gpu_poll_draw_scene_clips_sky_boundary(*sky_args,native_draw_boundary)
      else:sky_result=gpu.nf_owned_gpu_poll_draw_scene_clips_sky(*sky_args)
     else:sky_result=gpu.nf_owned_gpu_draw_scene_clips_sky(*sky_args)
    draw_stage("native_sky_draw_call")
    if sky_result==42:raise RuntimeError('Batched input poll failed')
    if sky_result:
     header=struct.unpack_from('<6I2Q',frame);offset=40+header[2]+header[3]
     mask=bytes(frame[offset+38400:offset+76800]);missing=[i for i in range(10560,25696) if not mask[i]]
     diagnostic=self.p/'prototype-runs/sky-rejected-sampled-frame.bin';diagnostic.write_bytes(frame)
     raise ValueError(f'Sky draw rejected code={sky_result} alpha={slot["alpha"]} fraction={sky_sample.weight} older={older_sky.serial} newer={newer_sky.serial} missing_count={len(missing)} first_missing={missing[:24]}')
   elif surface_bounds is not None:
    gpu.nf_owned_gpu_draw_scene_clips.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint]
    if self.diagnostic_async_timer:
     native_times=(C.c_uint64*2)()
     gpu.nf_owned_gpu_draw_scene_clips_timed.argtypes=gpu.nf_owned_gpu_draw_scene_clips.argtypes+[C.c_void_p]
     assert gpu.nf_owned_gpu_draw_scene_clips_timed(frame,len(frame),cm,models,surface_bounds,surface_detail['geometry_records'],native_times)==0
     native_draw_elapsed_ns=int(native_times[0]);native_draw_thread_cpu_ns=int(native_times[1]) if native_times[1]!=2**64-1 else None
    else:
     assert gpu.nf_owned_gpu_draw_scene_clips(frame,len(frame),cm,models,surface_bounds,surface_detail['geometry_records'])==0
   elif cm is None:assert gpu.nf_owned_gpu_draw(frame,len(frame))==0
   else:assert gpu.nf_owned_gpu_draw_poses(frame,len(frame),cm,models,len(models)//12)==0
   if sky_sample is not None and self.sky_wrap_limit and len(self.sky_wrap_captures)<self.sky_wrap_limit and abs(older_sky.boundary.source-newer_sky.boundary.source)>120:
    key=(older_sky.boundary.epoch,older_sky.serial,newer_sky.serial)
    if key not in self.sky_wrap_seen:
     from capture_live_sky_wrap import capture
     self.sky_wrap_captures.append(capture(gpu,frame,cm,models,surface_bounds,sky_sample,older_sky,newer_sky,slot['alpha'],slot['index']));self.sky_wrap_seen.add(key)
   draw_cycle_end=thread_cycles() if draw_cycle_begin is not None else None
   draw_end=time.perf_counter_ns();finish_ns=None;gpu_elapsed_ns=None
   texture_stats=None;decoded_stats=None
   if self.diagnostic_async_timer:
    texture=(C.c_uint64*6)();decoded=(C.c_uint64*3)()
    gpu.nf_owned_gpu_texture_stats.argtypes=[C.c_void_p];gpu.nf_owned_decoded_texture_stats.argtypes=[C.c_void_p]
    assert gpu.nf_owned_gpu_texture_stats(texture)==0;gpu.nf_owned_decoded_texture_stats(decoded)
    texture_stats=list(texture);decoded_stats=list(decoded)

   if async_query:
    assert gpu.nf_owned_gpu_timer_end()==0;gpu_query_end_ns=time.perf_counter_ns();self.pending_gpu_timer=len(self.results)
   if self.diagnostic_finish:
    assert gpu.nf_owned_gpu_timer_end()==0
    wait_begin=time.perf_counter_ns()
    assert gpu.nf_owned_gpu_finish()==0;finish_ns=time.perf_counter_ns()-wait_begin
    elapsed=C.c_uint64();gpu.nf_owned_gpu_timer_read.argtypes=[C.POINTER(C.c_uint64)]
    assert gpu.nf_owned_gpu_timer_read(C.byref(elapsed))==0 and elapsed.value>0
    gpu_elapsed_ns=elapsed.value
   end=time.perf_counter_ns()
   native_wait_times=None
   if native_callback_enabled and not self.diagnostic_async_timer and not self.diagnostic_finish:
    native_wait=(C.c_uint64*4)()
    wait_result=self.d.nf_owned_handoff_wait_token(self.owner,epoch,generation,slot['deadline_ns'],native_wait)
    assert wait_result in (0,1),wait_result;ready=wait_result==1;native_wait_times=list(native_wait)
   else:ready=self.wait_until(slot['deadline_ns'],wait_revision)
   if not ready:
    # Keep an unfinished native query occupied, but discard its canceled row.
    if async_query:self.pending_gpu_timer=-1
    return False
   present_begin=time.perf_counter_ns()
   callback_times[:]=[None,None,None]
   with self.presentation_publication_lock:
    native_sample=None;native_commit_stages=None
    if native_callback_enabled and not self.diagnostic_async_timer and not self.diagnostic_finish:
     native_sample=(C.c_uint64*8)()
     if self.native_commit_stages_enabled:
      native_commit_stages=(C.c_uint64*7)()
      committed=self.d.nf_owned_handoff_commit_sample_stages(self.owner,epoch,generation,previous[2],refresh,slot['index'],slot['alpha'],commit,commit_context,native_sample,native_commit_stages)
     else:
      committed=self.d.nf_owned_handoff_commit_sample(self.owner,epoch,generation,previous[2],refresh,slot['index'],slot['alpha'],commit,commit_context,native_sample)
    else:committed=(self.d.nf_owned_handoff_commit_token_timed(self.owner,epoch,generation,commit,commit_context,native_commit_ticks) if self.diagnostic_async_timer else self.d.nf_owned_handoff_commit_token(self.owner,epoch,generation,commit,commit_context))
    assert committed in (0,1),committed
    commit_return_ns=time.perf_counter_ns()
    if native_callback_enabled and committed:
     assert present_context.result==0
     native_present_time.value=present_context.elapsed_ns
    if (self.diagnostic_async_timer or self.native_commit_stages_enabled) and committed:assert gpu.nf_owned_gpu_present_stages(native_present_stages)==0
    self.results.append(dict(gpu_query_begin_ns=gpu_query_begin_ns,gpu_query_end_ns=gpu_query_end_ns,native_commit_stage_ns=list(native_commit_stages) if native_commit_stages is not None else None,native_committed_sample=list(native_sample) if native_sample is not None and committed else None,native_wait_timing=native_wait_times,input_draw_batched=batched_input,sky_hud_cache_stats=sky_hud_cache_stats,sky_hud_stage_ns=sky_hud_stages,sky_draw_stage_ns=sky_draw_stages,sky_phase_mode="continuous_angle" if self.sky_continuous else "original_offsets",sky_interpolated=sky_sample is not None,sky_fraction=sky_sample.weight if sky_sample else None,sky_source_older=older_sky.serial if sky_sample else None,sky_source_newer=newer_sky.serial if sky_sample else None,sky_slot_alpha=slot['alpha'] if sky_sample else None,sky_angle_older=older_sky.boundary.angle if sky_sample else None,sky_angle_newer=newer_sky.boundary.angle if sky_sample else None,sky_phase=((older_sky.boundary.angle&16383)+(((newer_sky.boundary.angle-older_sky.boundary.angle+8192)&16383)-8192)*slot['alpha'])*240/4096%240 if sky_sample else None,native_present_callback=native_callback_enabled,native_commit_ticks=list(native_commit_ticks) if self.diagnostic_async_timer else None,callback_enter_ns=callback_times[0],callback_exit_ns=callback_times[1],commit_return_ns=commit_return_ns,native_present_stage_ns=list(native_present_stages) if (self.diagnostic_async_timer or self.native_commit_stages_enabled) and committed else None,refresh=refresh,source_older=previous[2],epoch=epoch,context_count=self.context_counter(),consumer_thread=threading.get_ident(),cpu_call_ns=end-begin,timing_scope='pose_prepare_and_draw_cpu',draw_without_readback=True,hidden_window_presented=bool(committed),presentation_deadline_ns=slot['deadline_ns'],present_begin_ns=present_begin,present_end_ns=time.perf_counter_ns(),display_index=slot['index'],alpha=slot['alpha'],interpolated=True,generation=generation,pair_prepare_ns=pair_prepare_ns,complete_scene_pair_retained=owned_scene_pair,full_scene_sampled=surface_detail is not None,surface_detail=surface_detail,source_submitted_ns=submitted_ns,source_dequeued_ns=dequeued_ns,pair_begin_ns=pair_begin,pair_ready_ns=pair_ready_ns,native_input_stage_ns=list(native_poll_stages) if self.diagnostic_async_timer else None,native_input_poll_ns=native_poll_time.value if self.diagnostic_async_timer else None,native_present_ns=native_present_time.value if self.diagnostic_async_timer and committed else None,slot_begin_ns=slot_begin_ns,input_poll_ns=None if batched_input else begin-slot_begin_ns,draw_complete_ns=end,pacing_wait_ns=present_begin-end,sample_begin_ns=begin,pose_sample_cpu_ns=pose_end-begin,draw_cpu_ns=draw_end-pose_end,draw_thread_cycles=draw_cycle_end-draw_cycle_begin if draw_cycle_begin is not None else None,draw_scope_stages=draw_scope_stages,native_draw_boundary=list(native_draw_boundary) if native_draw_boundary is not None else None,native_draw_elapsed_ns=native_draw_elapsed_ns,native_draw_thread_cpu_ns=native_draw_thread_cpu_ns,gpu_completion_wait_ns=finish_ns,gpu_elapsed_ns=gpu_elapsed_ns,texture_stats=texture_stats,decoded_texture_stats=decoded_stats,gpu_timer_async=async_query,gpu_completed_before_present=finish_ns is not None))
    self.results[-1]['present_record_done_ns']=time.perf_counter_ns()
   if not committed:return False
  return True
 def consume(self):
  gpu=None;previous=None;priority=None
  try:
   from owned_thread_priority import ThreadPriorityLease
   priority=ThreadPriorityLease(self.renderer_thread_priority)
   gpu=C.CDLL(str(self.p/((self.sky_renderer_candidate or getattr(type(self),'gpu_renderer_name','owned-sky-gpu.dll')) if self.sky_interpolate else 'owned-world-gpu.dll')));gpu.nf_owned_gpu_render.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t];gpu.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];gpu.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];gpu.nf_owned_gpu_present.argtypes=[C.c_uint64]
   # Pure immediate native counter read: retain GIL for this call only.
   # Drawing, input, lifecycle and driver operations still use CDLL.
   self.context_counter=C.PYFUNCTYPE(C.c_uint)(C.cast(gpu.nf_owned_gpu_contexts,C.c_void_p).value)
   self.context_creation_base=self.context_counter()
   if self.present:
    assert gpu.nf_owned_gpu_window(int(self.show_window))==0
    gpu.nf_owned_gpu_swap_interval.argtypes=[C.c_int,C.c_void_p]
    swap=(C.c_int*2)();swap_result=gpu.nf_owned_gpu_swap_interval(-1 if self.swap_interval is None else self.swap_interval,swap)
    self.swap_interval_observed=dict(result=swap_result,before=swap[0] if swap_result==0 else None,after=swap[1] if swap_result==0 else None)
    if self.swap_interval is not None:assert swap_result==0,self.swap_interval_observed
    gpu.nf_owned_input_snapshot.argtypes=[C.c_void_p]
    assert gpu.nf_owned_input_poll()
    self.input_gpu=gpu;self.input_ready.set()
   previous_frame_free_ns=None;previous_frame_free_execution=None
   while True:
    loop_started_ns=time.perf_counter_ns()
    if self.present:assert gpu.nf_owned_input_poll()
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
     wait_revision=self.pause_revision
     rgb=C.create_string_buffer(3840*2160*3) if self.verify else None;begin=time.perf_counter_ns()
     if self.draw_only:
      assert gpu.nf_owned_gpu_draw(owner,size.value)==0;end=time.perf_counter_ns()
      if self.present:
       deadline=None
       if self.paced and self.clock_origin is not None:
        ticks=(refresh-self.clock_base+self.delay_refreshes)*280896
        deadline=self.clock_origin+(ticks*1000000000+16777215)//16777216
        if not self.wait_until(deadline,wait_revision):previous=None;continue
       assert gpu.nf_owned_gpu_present(epoch+1)==32
       Callback=C.CFUNCTYPE(C.c_int,C.c_void_p)
       commit=Callback(lambda ctx:gpu.nf_owned_gpu_present(epoch)==0)
       self.d.nf_owned_handoff_commit_token.argtypes=[C.c_void_p,C.c_uint64,C.c_uint64,Callback,C.c_void_p]
       present_begin=time.perf_counter_ns();committed=self.d.nf_owned_handoff_commit_token(self.owner,epoch,generation.value,commit,None);assert committed in (0,1);present_end=time.perf_counter_ns()
      if self.verify:assert gpu.nf_owned_gpu_read(rgb,len(rgb))==0
     else:
      assert gpu.nf_owned_gpu_render(owner,size.value,rgb,len(rgb))==0;end=time.perf_counter_ns()
     if self.verify:
      reference=(self.p/f'owned-timed-{refresh}.ppm').read_bytes().split(b'\n',3)[3];assert rgb.raw==reference
     self.results.append(dict(refresh=refresh,epoch=epoch,sha256=hashlib.sha256(rgb.raw).hexdigest() if self.verify else None,context_count=self.context_counter(),cpu_call_ns=end-begin,timing_scope="draw_submission_cpu" if self.draw_only else "draw_and_readback_cpu",draw_without_readback=self.draw_only,hidden_window_presented=bool(committed) if self.present else False,consumer_thread=threading.get_ident(),presentation_deadline_ns=deadline if self.present else None,present_begin_ns=present_begin if self.present else None,present_end_ns=present_end if self.present else None))
     if self.interpolate:previous=(current,generation.value,refresh,scene) if committed else None
     self.first_frame_ready.set()
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
    if self.diagnostic_async_timer or self.gpu_query_only:self.poll_gpu_timer(gpu)
    if hasattr(self,'_before_gpu_close'):
     try:self._before_gpu_close()
     except Exception as failure:self.errors.append(repr(failure))
    if not gpu.nf_owned_gpu_close():self.errors.append("Native GPU/input shutdown failed; controller worker or context resources retained")
    if hasattr(self,"_after_gpu_close"):
     try:self._after_gpu_close(gpu)
     except Exception as failure:self.errors.append(repr(failure))
    if hasattr(gpu,'nf_owned_gpu_query_pending'):
     self.gpu_queries_after_close=gpu.nf_owned_gpu_query_pending()
     if self.gpu_queries_after_close:self.errors.append('GPU timestamp queries retained after close')
    if hasattr(gpu,'nf_owned_gpu_active_contexts'):
     self.active_contexts_after_close=gpu.nf_owned_gpu_active_contexts()
     if self.active_contexts_after_close:self.errors.append("Graphics context retained after shutdown")
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
  if hasattr(self.d,'nf_owned_handoff_pool_stats'):
   pool_stats=(C.c_uint64*4)();fn=self.d.nf_owned_handoff_pool_stats;fn.argtypes=[C.c_void_p,C.c_void_p];fn.restype=C.c_int
   assert fn(self.owner,pool_stats)
   self.handoff_pool_stats=dict(allocations=pool_stats[0],reuses=pool_stats[1],cached_buffers=pool_stats[2],cached_bytes=pool_stats[3],consumer_joined=not self.thread.is_alive())
  self.d.nf_owned_handoff_destroy(self.owner);self.owner=None
  with self.scene_snapshot_lock:self.scene_snapshots.clear();self.resume_scene_chain.clear();self.pause_replay_plan=None
  self.shutdown_evidence=dict(preparation_service_shutdown=getattr(self.preparation_service,"shutdown_evidence",None),open_pause=open_pause,close_completed_ns=time.perf_counter_ns(),dxgi_shutdown=getattr(self,'dxgi_shutdown',None),gpu_queries_after_close=getattr(self,'gpu_queries_after_close',None),notification_queue_released=not hasattr(self.signals,'owner') or self.signals.owner is None,gpu_fences_after_close=getattr(self,'gpu_fences_after_close',None),active_contexts_after_close=getattr(self,'active_contexts_after_close',None),context_creation_base=getattr(self,'context_creation_base',None),gpu_thread_alive=self.thread.is_alive(),native_owner_released=self.owner is None,retained_scene_count=len(self.resume_scene_chain.items),pending_scene_count=len(self.scene_snapshots),preparation_thread_alive=self.preparation_service.pipeline.thread.is_alive() if self.preparation_service is not None and hasattr(self.preparation_service,'pipeline') else None,prepared_result_count=len(self.preparation_service.pipeline.ready) if self.preparation_service is not None and hasattr(self.preparation_service,'pipeline') else None)
  if self.errors:raise RuntimeError(self.errors)
  assert (self.expected_frames is None or len(self.results)==self.expected_frames) and all(r['consumer_thread']!=self.producer and r['context_count']==self.context_creation_base+1 for r in self.results)



