"""Experimental full-scene native draw/wait/commit worker; default unchanged."""
import ctypes as C,time,struct,threading,os
from concurrent.futures import CancelledError
from live_owned_gpu_worker import LiveOwnedGPUWorker
from owned_motion_clock import scene_samples
from owned_thread_cycles import read as thread_cycles
P=C.c_void_p;U=C.c_uint64;Callback=C.CFUNCTYPE(C.c_int,P)
U4,U16,U32,U40,U48,U64,U128=(U*n for n in (4,16,32,40,48,64,128))
def callback_address(function):
 # Library/callback owners remain live for every synchronous native call.
 # Reading pointer storage avoids ctypes.cast ownership back-links.
 return P.from_buffer(function).value

LeaseAcquire=C.CFUNCTYPE(C.c_int,C.POINTER(U));LeaseSelect=C.CFUNCTYPE(C.c_int,U,U);LeaseToken=C.CFUNCTYPE(C.c_int,U)
class DrawContext(C.Structure):
 _fields_=[('frame',P),('bytes',C.c_size_t),('camera',P),('models',P),('bounds',P),('count',C.c_uint),('lower',P),('upper',P),('skycount',C.c_size_t),('weight',C.c_double),('result',C.c_int),('started_ns',U),('completed_ns',U),('thread_cycles',U)]
class PresentContext(C.Structure):_fields_=[('epoch',U),('timed',C.c_uint32),('result',C.c_int32),('elapsed_ns',U)]
class PresentProfile(C.Structure):
 _fields_=[('present',P),('context',P),('read',P),('stages',U*3),('result',C.c_int),('completion_read',P),('completion',U*3),('completion_result',C.c_int),('fence_enabled',C.c_int),('fence',U*8),('cpu_read',P),('cpu',U*4),('cpu_result',C.c_int),('query_read',P),('queries',U*104),('query_result',C.c_int)]
class SourceBatchWorker(LiveOwnedGPUWorker):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs)
  self.slow_hud_capture=None
  if getattr(type(self),"slow_hud_capture_ns",0):
   from owned_slow_hud_capture import SlowHudCapture
   self.slow_hud_capture=SlowHudCapture()
  self.dxgi_bridge=None
  if getattr(type(self),'dxgi_enabled',False) or os.environ.get('NF_BATCH_DXGI_PRESENT')=='1':
   self.dxgi_bridge=C.CDLL(str(self.p/getattr(type(self),'dxgi_bridge_name','owned-dx-present-bridge.dll')))
   self.dxgi_bridge.nf_dx_bridge_stats.argtypes=[P]
  from owned_active_batch_publication import ActiveBatchPublication
  self.batch_publication=ActiveBatchPublication()
  self.batch_bridge=C.CDLL(str(self.p/getattr(type(self),'batch_bridge_name','owned-batch-present-candidate.dll')))
  self.gpu_ready_enabled=bool(getattr(type(self),'gpu_ready_enabled',False))
  self.ready_adapter=None
  self.gpu_queued_enabled=bool(getattr(type(self),"gpu_queued_enabled",False))
  assert not (self.gpu_queued_enabled and self.gpu_ready_enabled)
  self.native_batch=self.batch_bridge.nf_owned_handoff_batch_queued if self.gpu_queued_enabled else self.batch_bridge.nf_owned_handoff_batch_ready if self.gpu_ready_enabled else self.batch_bridge.nf_owned_handoff_batch
  self.native_batch.argtypes=[P,U,U,P,C.c_uint,Callback,Callback,P,P,P,P]+([LeaseAcquire,LeaseSelect,LeaseToken,LeaseToken] if self.gpu_queued_enabled else [Callback,P] if self.gpu_ready_enabled else [])
  self.profile_bridge=C.CDLL(str(self.p/'owned-present-profile-bridge.dll'))
  self.profile_bridge.nf_owned_profile_size.restype=C.c_size_t
  assert self.profile_bridge.nf_owned_profile_size()==C.sizeof(PresentProfile)
  self.profile_callback=Callback(callback_address(self.profile_bridge.nf_owned_profile_present))
  self.registration_bridge=C.PyDLL(str(self.p/getattr(type(self),'batch_bridge_name','owned-batch-present-candidate.dll')))
  self.registration_bridge.nf_owned_handoff_commit_token.argtypes=[P,U,U,Callback,P]

 def close(self):
  try:super().close()
  finally:
   if not self.thread.is_alive() and hasattr(self.results,"flush"):
    self.results.flush();self.compact_presentation_diagnostic_stats=self.results.stats()
    self.results=self.results.snapshot()

  if self.slow_hud_capture is not None:
   self.slow_hud_capture_manifest=self.slow_hud_capture.save(self.p/"prototype-runs"/("slow-hud-"+str(time.time_ns())))

 def _before_gpu_close(self):
  if hasattr(self,'crop_ledger'):self.crop_ledger.retire();self.async_crop_report=self.crop_ledger.report()
  if self.ready_adapter is not None:
   assert self.ready_adapter.nf_gpu_ready_close()==0
   stats=U4();self.ready_adapter.nf_gpu_ready_stats.argtypes=[P];assert self.ready_adapter.nf_gpu_ready_stats(stats)==0
   assert stats[0]==stats[1] and stats[3]==0
   self.gpu_ready_shutdown=list(stats)
  if getattr(self,'dxgi_bridge',None) is not None:
   stats=U4();assert self.dxgi_bridge.nf_dx_bridge_stats(stats)==0
   assert stats[1]==stats[2]==0,'Live DXGI unexpectedly used readback'
   assert self.dxgi_bridge.nf_dx_bridge_close()==0
   self.dxgi_shutdown=dict(stats=list(stats),active_after_close=self.dxgi_bridge.nf_dx_bridge_active())
   assert self.dxgi_shutdown['active_after_close']==0
  if not self.profile_bridge.nf_owned_profile_fences_clear():raise RuntimeError('GPU diagnostic fence owner mismatch')
  self.gpu_fences_after_close=self.profile_bridge.nf_owned_profile_fences_pending()
  assert self.gpu_fences_after_close==0

 def register_native_batch(self,epoch,generation,metadata,owned):
  tokens=[]
  def register(ctx):
   tokens.append(self.batch_publication.begin(epoch,generation,metadata,owned));return 1
  callback=Callback(register)
  valid=self.registration_bridge.nf_owned_handoff_commit_token(self.owner,epoch,generation,callback,None)
  if valid==0:return None
  assert valid==1 and len(tokens)==1
  return tokens[0]

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
  if not hasattr(self,'draw_commit_bridge'):
   self.draw_commit_bridge=C.CDLL(str(self.p/'owned-draw-commit-candidate.dll'))
   self.draw_commit_bridge.nf_owned_handoff_draw_wait_commit_sample.argtypes=[P,U,U,U,U,U,C.c_double,U,Callback,P,Callback,P,P,P,P]
  transaction=self.draw_commit_bridge.nf_owned_handoff_draw_wait_commit_sample
  draw_callback=Callback(callback_address(gpu.nf_owned_gpu_source_context_callback));present_callback=Callback(callback_address(gpu.nf_owned_gpu_present_callback))
  dxgi=getattr(self,'dxgi_bridge',None) is not None
  if dxgi:present_callback=Callback(callback_address(self.dxgi_bridge.nf_dx_bridge_present_context_callback))
  if dxgi and getattr(type(self),'dxgi_scene_timer_enabled',False):
   self.dxgi_bridge.nf_dx_scene_set_draw.argtypes=[P]
   assert self.dxgi_bridge.nf_dx_scene_set_draw(callback_address(draw_callback))==0
   draw_callback=Callback(callback_address(self.dxgi_bridge.nf_dx_scene_draw_callback))
  ready_callback=None
  if self.gpu_ready_enabled:
   assert not dxgi and not getattr(self,'present_completion_barrier',False)
   if self.ready_adapter is None:self.ready_adapter=C.CDLL(str(self.p/getattr(type(self),'ready_adapter_name','owned-gpu-ready-adapter.dll')))
   self.ready_adapter.nf_gpu_ready_set_draw.argtypes=[P]
   assert self.ready_adapter.nf_gpu_ready_set_draw(callback_address(draw_callback))==0
   draw_callback=Callback(callback_address(self.ready_adapter.nf_gpu_ready_draw))
   ready_callback=Callback(callback_address(self.ready_adapter.nf_gpu_ready_poll))
  gpu.nf_owned_gpu_draw_context_size.restype=C.c_size_t;assert gpu.nf_owned_gpu_draw_context_size()==C.sizeof(DrawContext)
  gpu.nf_owned_gpu_present_stages.argtypes=[P]
  query_enabled=bool(getattr(self,'gpu_timestamp_probe_enabled',False))
  if self.gpu_queued_enabled:assert not dxgi and not query_enabled and not getattr(self,"gpu_fence_probe_enabled",False),"Queued slot diagnostics require per-token query attribution"
  if dxgi:assert not query_enabled and not getattr(self,'gpu_fence_probe_enabled',False) and not getattr(self,'present_completion_barrier',False),'DXGI backend requires separate diagnostic probes'
  assert gpu.nf_owned_gpu_query_mode(int(query_enabled))==0
  ordered_gpu=self.gpu_queued_enabled and bool(getattr(type(self),"queued_ordered_gpu",False))
  slot_queries=self.gpu_queued_enabled and bool(getattr(type(self),"queued_query_enabled",False))
  assert not (ordered_gpu and slot_queries),"GPU results may be unavailable before ordered submission"
  if self.gpu_queued_enabled:
   gpu.nf_owned_gpu_target_query_mode.argtypes=[C.c_int];assert gpu.nf_owned_gpu_target_query_mode(int(slot_queries))==0
   self.batch_bridge.nf_owned_queued_set_query.argtypes=[P];assert self.batch_bridge.nf_owned_queued_set_query(callback_address(gpu.nf_owned_gpu_target_query) if slot_queries else None)==1
  completion_enabled=bool(getattr(self,"present_completion_barrier",False))
  gpu.nf_owned_gpu_present_completion_read.argtypes=[P]
  assert gpu.nf_owned_gpu_present_completion_mode(int(completion_enabled))==0
  from owned_source_presentation_batch_candidate import OwnedSourcePresentationBatch
  slots=[slot for slot in scene_samples(self.clock_origin,self.clock_base,previous[2],refresh,self.delay_refreshes) if slot['index']>self.resume_cutoff]
  if not slots:return True
  rows=[];metadata=[];sample_preparation=[]
  old=previous[3].sky;new=scene.sky
  if old is None or new is None or old.asset is None:raise ValueError('Missing paired sky')
  begin=time.perf_counter_ns()
  for slot in slots:
   sample_start=time.perf_counter_ns();sample_cycles=thread_cycles()
   value=pair.sample(slot['alpha'])
   scene_ready=time.perf_counter_ns();scene_cycles=thread_cycles()
   sky=old.asset.sample_continuous(old.boundary,new.boundary,slot['alpha'])
   sky_ready=time.perf_counter_ns();sky_cycles=thread_cycles()
   sample_preparation.append(dict(display_index=slot['index'],scene_started_ns=sample_start,scene_ready_ns=scene_ready,sky_ready_ns=sky_ready,scene_thread_cycles=scene_cycles-sample_cycles,sky_thread_cycles=sky_cycles-scene_cycles))
   rows.append((previous[2],refresh,slot['index'],slot['deadline_ns'],slot['alpha'],value,sky))
   metadata.append(dict(epoch=epoch,generation=generation,source_older=previous[2],refresh=refresh,display_index=slot['index'],alpha=slot['alpha']))
  owner_begin=time.perf_counter_ns();owner_cycles=thread_cycles()
  owned=OwnedSourcePresentationBatch(epoch,rows,pair,gpu)
  owner_ready=time.perf_counter_ns();owner_cycle_cost=thread_cycles()-owner_cycles
  fence_enabled=bool(getattr(self,'gpu_fence_probe_enabled',False) or os.environ.get('NF_BATCH_GPU_FENCES')=='1')
  profiles=(PresentProfile*len(slots))()
  for i in range(len(slots)):
   profiles[i].present=callback_address(present_callback);profiles[i].context=owned.items[i].presentctx;profiles[i].read=callback_address(gpu.nf_owned_gpu_present_stages);profiles[i].completion_read=callback_address(gpu.nf_owned_gpu_present_completion_read)
   profiles[i].query_read=callback_address(gpu.nf_owned_gpu_query_read)
   profiles[i].cpu_read=callback_address(gpu.nf_owned_gpu_present_cpu_stages)
   profiles[i].fence_enabled=int(fence_enabled)
   if not dxgi:owned.items[i].presentctx=C.addressof(profiles[i])
  batch=self.native_batch
  registration_requested=time.perf_counter_ns()
  with self.presentation_publication_lock:
   registration_acquired=time.perf_counter_ns()
   token=self.register_native_batch(epoch,generation,metadata,owned)
   if token is None:return False
   registration_completed=time.perf_counter_ns()
  called=time.perf_counter_ns()
  extra=[ready_callback,None] if self.gpu_ready_enabled else []
  draw_probed=self.gpu_queued_enabled and bool(getattr(type(self),"queued_draw_probe_enabled",False))
  if self.gpu_queued_enabled:
   self.batch_bridge.nf_owned_queued_set_draw_probe.argtypes=[P];assert self.batch_bridge.nf_owned_queued_set_draw_probe(callback_address(gpu.nf_owned_gpu_target_draw_probe) if draw_probed else None)==1
   from owned_async_crop_ledger import CropLedger
   if not hasattr(self,'crop_ledger'):self.crop_ledger=CropLedger(gpu,limit=getattr(type(self),"async_crop_limit",120))
   selected_position=[0]
   gpu.nf_owned_gpu_target_select.argtypes=[U,U]
   def capture_selected(target,selected_epoch):
    rc=gpu.nf_owned_gpu_target_select(target,selected_epoch)
    if rc:return rc
    position=selected_position[0];selected_position[0]+=1
    if position>=len(metadata):return 37
    try:
     self.crop_ledger.poll()
     if metadata[position]['display_index']>=int(os.environ.get('NF_ASYNC_CROP_START_INDEX','180')):self.crop_ledger.enqueue(metadata[position],target,selected_epoch)
    except Exception as error:
     self.async_crop_error=repr(error);return 37
    return 0
   extra=[LeaseAcquire(callback_address(gpu.nf_owned_gpu_target_acquire)),LeaseSelect(capture_selected),LeaseToken(callback_address(gpu.nf_owned_gpu_target_release)),LeaseToken(callback_address(gpu.nf_owned_gpu_target_ordered if ordered_gpu else gpu.nf_owned_gpu_target_ready))]
  result=batch(self.owner,epoch,generation,owned.items,len(slots),draw_callback,present_callback if dxgi else self.profile_callback,owned.samples,owned.waits,owned.stages,C.byref(owned.completed),*extra)
  returned=time.perf_counter_ns()
  queued_times=None;queued_cpu=None;queued_queries=None;queued_observations=None;draw_profiles=None;draw_cpu=None
  if self.gpu_queued_enabled:
   queued_times=U64();self.batch_bridge.nf_owned_queued_timing.argtypes=[P];assert self.batch_bridge.nf_owned_queued_timing(queued_times)==1
   queued_cpu=U32();self.batch_bridge.nf_owned_queued_cpu.argtypes=[P];assert self.batch_bridge.nf_owned_queued_cpu(queued_cpu)==1
   queued_observations=U64();self.batch_bridge.nf_owned_queued_observations.argtypes=[P];assert self.batch_bridge.nf_owned_queued_observations(queued_observations)==1
   if slot_queries:
    queued_queries=U64();self.batch_bridge.nf_owned_queued_queries.argtypes=[P];assert self.batch_bridge.nf_owned_queued_queries(queued_queries)==1
  if draw_probed:
   draw_profiles=U128();draw_cpu=U16();self.batch_bridge.nf_owned_queued_draw_profiles.argtypes=[P];self.batch_bridge.nf_owned_queued_draw_cpu.argtypes=[P]
   assert self.batch_bridge.nf_owned_queued_draw_profiles(draw_profiles)==1 and self.batch_bridge.nf_owned_queued_draw_cpu(draw_cpu)==1
  ready_times=None;ready_breakdown=None;ready_handles=None
  if self.gpu_ready_enabled:
   ready_times=U40();self.batch_bridge.nf_owned_ready_timing.argtypes=[P]
   assert self.batch_bridge.nf_owned_ready_timing(ready_times)==1
   ready_breakdown=U48();self.batch_bridge.nf_owned_ready_breakdown.argtypes=[P]
   assert self.batch_bridge.nf_owned_ready_breakdown(ready_breakdown)==1
   if hasattr(self.batch_bridge,"nf_owned_ready_handles"):
    ready_handles=U4();self.batch_bridge.nf_owned_ready_handles.argtypes=[P]
    assert self.batch_bridge.nf_owned_ready_handles(ready_handles)==1 and ready_handles[0]==ready_handles[1]
  with self.presentation_publication_lock:
   prefix=[list(owned.samples[i*8:(i+1)*8]) for i in range(owned.completed.value)]
   published=self.batch_publication.finish(token,prefix)
   for i,row in enumerate(published):
    ctx=owned.draws[i];pc=owned.presents[i];slot=slots[i];stages=list(owned.stages[i*7:(i+1)*7]);wait=list(owned.waits[i*4:(i+1)*4])
    assert ctx.result==pc.result==0
    self.results.append(dict(row,native_batch_candidate=True,native_transaction_candidate=True,consumer_thread=threading.get_ident(),context_count=self.context_counter(),interpolated=True,hidden_window_presented=True,full_scene_sampled=True,complete_scene_pair_retained=True,sky_interpolated=True,sky_phase_mode='continuous_angle',sky_fraction=rows[i][-1].weight,native_present_stage_ns=list(profiles[i].stages),native_present_thread_cycles=list(profiles[i].cpu),native_present_cpu_result=profiles[i].cpu_result,gpu_timestamp_probe=list(profiles[i].queries),gpu_timestamp_result=profiles[i].query_result,native_present_profile_result=profiles[i].result,native_present_completion=list(profiles[i].completion),native_present_completion_result=profiles[i].completion_result,present_completion_barrier=completion_enabled,gpu_fence_probe_enabled=fence_enabled,gpu_fence_probe=list(profiles[i].fence),native_commit_stage_ns=stages,native_wait_timing=wait,presentation_deadline_ns=slot['deadline_ns'],present_begin_ns=stages[0],present_end_ns=row['native_committed_sample'][6],commit_return_ns=returned,sample_begin_ns=ctx.started_ns,batch_preparation_begin_ns=begin,batch_native_call_ns=called,batch_native_return_ns=returned,batch_sample_count=len(slots),batch_sample_position=i,batch_registration_ns=[owner_ready,registration_requested,registration_acquired,registration_completed,called] if i==0 else None,batch_preparation_stages=sample_preparation if i==0 else None,batch_packaging_stages=owned.packaging_stages if i==0 else None,batch_owner_stage=dict(started_ns=owner_begin,completed_ns=owner_ready,thread_cycles=owner_cycle_cost) if i==0 else None,draw_complete_ns=ctx.completed_ns,draw_cpu_ns=ctx.completed_ns-ctx.started_ns,native_draw_boundary=[ctx.started_ns,ctx.completed_ns,ctx.thread_cycles,0],transaction_begin_ns=called,transaction_return_ns=returned,pair_begin_ns=pair_begin,pair_ready_ns=pair_ready_ns,pair_prepare_ns=pair_prepare_ns,source_submitted_ns=submitted_ns,source_dequeued_ns=dequeued_ns,surface_detail=rows[i][5][4],native_present_callback=True,input_draw_batched=True))
    if self.gpu_queued_enabled:self.results[-1].update(native_queued_targets=True,gpu_completion_wait_enabled=not ordered_gpu,queued_lookahead_capacity=3,gpu_query_attribution_verified=False,queued_stage_timing=list(queued_times[i*8:(i+1)*8]),queued_readiness_thread_cpu=list(queued_cpu[i*4:(i+1)*4]),queued_fence_observations=list(queued_observations[i*8:(i+1)*8]))
    if queued_queries is not None:self.results[-1].update(queued_slot_gpu_query=list(queued_queries[i*8:(i+1)*8]),gpu_query_attribution_verified=True)
    if draw_profiles is not None:self.results[-1].update(queued_draw_stage_profile=list(draw_profiles[i*16:(i+1)*16]),queued_draw_thread_cpu=list(draw_cpu[i*2:(i+1)*2]))
    if ready_times is not None:self.results[-1].update(gpu_ready_timing=list(ready_times[i*5:(i+1)*5]),gpu_ready_breakdown=list(ready_breakdown[i*6:(i+1)*6]))
    if ready_handles is not None and i==0:self.results[-1]["gpu_ready_handles"]=list(ready_handles)
    if dxgi:
     self.results[-1].update(presentation_backend='dxgi_flip_sequential',dxgi_present_elapsed_ns=owned.presents[i].elapsed_ns,dxgi_present_result=owned.presents[i].result)
     for key in ('native_present_stage_ns','native_present_thread_cycles','native_present_cpu_result','gpu_timestamp_probe','gpu_timestamp_result','native_present_profile_result','native_present_completion','native_present_completion_result','gpu_fence_probe'):
      self.results[-1][key]=None
  if self.slow_hud_capture is not None and draw_profiles is not None:
   for i in range(owned.completed.value):
    profile=list(draw_profiles[i*16:(i+1)*16])
    if profile[8]>=type(self).slow_hud_capture_ns:self.slow_hud_capture.add(metadata[i],rows[i][5],rows[i][6],profile)
  assert result in (0,1),result
  return result==1

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
   active=self.batch_publication.active
   batch_generation=active[2] if active else int(native[1])
   resolved=self.batch_publication.snapshot(native,1,self.epoch,batch_generation)
   published=resolved['last_committed']
   committed=published

  return dict(retained_chain_refreshes=retained,snapshot_refreshes=snapshots,prepared_intervals=prepared,last_submitted_refresh=previous[1].identity[1] if previous else None,last_committed={key:committed.get(key) for key in ('refresh','source_older','display_index','alpha','generation','present_end_ns')} if committed else None,pause_revision=self.pause_revision)

