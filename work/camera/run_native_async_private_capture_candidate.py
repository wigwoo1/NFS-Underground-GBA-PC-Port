import owned_async_handoff_worker_install_candidate
from owned_producer_caller_gap_candidate import ProducerDeadlineRows
import owned_scenery_thread_library_install_candidate
import owned_visibility_thread_library_install_candidate
"""Isolated recent diagnostic window; explicit whole-run counters in report."""
import sys,os,ctypes as C
from owned_segmented_display_placement_install_candidate import progress,diagnostic_stats
import owned_endpoint_road_planner as planner_module
from owned_endpoint_road_fixed_types_candidate import endpoint_road_span_candidates
planner_module.endpoint_road_span_candidates=endpoint_road_span_candidates
import owned_viewport_bounds_fixed_types_install_candidate
from pathlib import Path
from owned_serialized_recent_rows_candidate import RecentRows
from owned_serialized_recent_rows_candidate import RecentRows as SerializedRows
from owned_pause_window_candidate import PauseWindow
from owned_recent_mutable_timings_candidate import RecentMutableTimingRows
from owned_producer_totals_candidate import DurationTotals
from owned_producer_long_scene_candidate import ProducerRows
import live_owned_gpu_worker,owned_world_preparation_service
import owned_world_preparation_service as process_module
from owned_bounded_diagnostics_candidate import BoundedPresentationDiagnostics
import owned_source_presentation_batch_candidate as source_batch
from owned_source_depth_transition_candidate import SourceFaceDeterminants
source_batch.SourceFaceDeterminants=SourceFaceDeterminants
from owned_d3d_profile_interval_totals_candidate import LongIntervalTotals as PresentationIntervalTotals
import copy
from owned_sky_motion_totals_candidate import SkyMotionTotals
from owned_native_callback_identity_candidate import validate as validate_native_row
class CheckedRecentPresentations(BoundedPresentationDiagnostics):
 def __init__(self,producer,contexts,**kwargs):super().__init__(**kwargs);self.producer=producer;self.contexts=contexts;self.intervals=PresentationIntervalTotals();self.sky_totals=SkyMotionTotals()
 def append(self,row):
  assert row['consumer_thread']!=self.producer and row['context_count']==self.contexts
  validate_native_row(row)
  previous=self.tail
  super().append(row)
  if previous is not None:self.intervals.observe(previous);self.sky_totals.observe(previous)
 def stats(self):
  out=super().stats();out['whole_run_thread_context_checked']=True;out['whole_run_native_identity_checked']=True
  totals=copy.copy(self.intervals)
  if self.tail is not None:totals.observe(self.tail)
  out['whole_run_api_intervals']=totals.stats();sky=copy.copy(self.sky_totals)
  if self.tail is not None:sky.observe(self.tail)
  out['whole_run_sky_motion']=sky.stats();return out
from live_native_hud_prefetch_generation_candidate import NativeLiveWorker as Base
from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
from owned_prepared_world_segmented_candidate import PreparedWorldMotion
process_module.PreparedWorldMotion=PreparedWorldMotion
from owned_preparation_release_candidate import PreparationPipeline
process_module.PreparationPipeline=PreparationPipeline
class BoundedService(process_module.WorldPreparationService):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);self.stage_samples=SerializedRows(60,max_record_bytes=1048576);self.pipeline.timings=RecentMutableTimingRows(60)
  if hasattr(self,'process') and os.environ.get('NFS_MEMORY_CHILD_FILE'):Path(os.environ['NFS_MEMORY_CHILD_FILE']).write_text(str(self.process.pid))
 def close(self):
  try:
   try:self.pipeline.close()
   finally:
    if self.history is not None:self.history.close();self.history=None
  finally:
   self.preparation_retention=self.stage_samples.stats();self.stage_samples=self.stage_samples.snapshot();self.queue_retention=self.pipeline.timings.stats();self.pipeline.timings=self.pipeline.timings.snapshot()
class BoundedWorker(Base):
 handoff_library_name="owned-handoff-request-authority-candidate.dll"
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs)
  self.frame_matches=self.d.nf_owned_frame_matches
  self.frame_matches.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t];self.frame_matches.restype=C.c_int
  self.pause_events=PauseWindow();self.world_resets=RecentRows(60)
  self.boundary_stage_samples=RecentRows(60,max_record_bytes=1048576);self.submit_stage_samples=RecentRows(60)
  self.results=CheckedRecentPresentations(self.producer,0,max_records=120,max_bytes=1024*1024)
 def close(self):
  try:super().close()
  finally:
   library=C.CDLL(str((Path('work/camera')/'owned-gpu-source-packet-profile-candidate.dll').resolve()))
   stats=(C.c_uint64*3)();assert library.nf_hud_owner_stats(stats)==1
   library.nf_hud_authority_reuses.restype=C.c_uint64
   cache=(C.c_uint64*3)();assert library.nf_hud_cache_lease_stats(cache)==1
   self.hud_lease_cleanup=dict(owner_stats=list(stats),authority_reuses=library.nf_hud_authority_reuses(),cache_lease=list(cache));assert list(stats)==[0,0,0] and cache[0]==0 and cache[1]==0 and cache[2]==0
   self.pause_retention=self.pause_events.stats();self.pause_events=self.pause_events.snapshot();self.reset_retention=self.world_resets.stats();self.world_resets=self.world_resets.snapshot();self.results=self.results.snapshot();self.boundary_retention=self.boundary_stage_samples.stats();self.boundary_stage_samples=self.boundary_stage_samples.snapshot();self.submit_retention=self.submit_stage_samples.stats();self.submit_stage_samples=self.submit_stage_samples.snapshot()
if __name__=='__main__':
 import owned_hud_cache_lease_worker_install_candidate
 import owned_renderer_dispatch_trace_install_candidate
 import owned_present_stage_trace_install_candidate
 import owned_renderer_fixed_types_install_candidate
 import owned_hud_prefetch_d3d_profile_install_candidate
 import owned_packet_profile_install_candidate
 import owned_d3d_call_profile_install_candidate
 process_module.WorldPreparationService=BoundedService
 live_owned_gpu_worker.WorldPreparationService=BoundedService
 owned_world_preparation_service.PrecomputedWorldSamples=PrecomputedSourceWorldSamples
 live_owned_gpu_worker.LiveOwnedGPUWorker=BoundedWorker
 path=Path('work/camera/run_owned_native_prototype.py');source=path.read_text()
 assert source.count(' def submit_latest():')==1
 source=source.replace(' def submit_latest():',' def submit_latest_impl():')
 marker=' from owned_smoke_pause_schedule import SmokePauseSchedule'
 assert source.count(marker)==1
 wrapper=" def submit_latest():\n  import owned_producer_caller_gap_candidate as caller_gap\n  begin=time.perf_counter_ns()\n  try:return submit_latest_impl()\n  finally:caller_gap.submission(begin,time.perf_counter_ns())\n"
 source=source.replace(marker,wrapper+marker)
 source=source.replace('report=dict(thread_native_frame_join_enabled=',"report=dict(handoff_pool_stats=getattr(worker,'handoff_pool_stats',None),dxgi_display_progress=progress.stats(),dxgi_raw_diagnostics=diagnostic_stats(),pause_retention=getattr(worker,'pause_retention',None),reset_retention=getattr(worker,'reset_retention',None),queue_retention=getattr(worker.preparation_service,'queue_retention',None),boundary_retention=getattr(worker,'boundary_retention',None),submit_retention=getattr(worker,'submit_retention',None),thread_native_frame_join_enabled=")
 old='presentations=len(worker.results),'
 assert source.count(old)==1
 source=source.replace(old,"presentations=getattr(worker,'bounded_diagnostic_stats',{}).get('total_records',len(worker.results)),bounded_diagnostic_stats=getattr(worker,'bounded_diagnostic_stats',None),")
 assert source.count('inputs=[];startup_inputs=[]')==1
 source=source.replace('inputs=[];startup_inputs=[]','inputs=RecentRows();startup_inputs=[]')
 source=source.replace('len(inputs)','inputs.total_records')
 assert source.count('original_update_samples=[];')==1
 source=source.replace('original_update_samples=[];','original_update_samples=ProducerDeadlineRows();')
 source=source.replace('original_update_samples=original_update_samples,','original_update_samples=original_update_samples.snapshot(),original_update_retention=original_update_samples.stats(),')
 source=source.replace('inputs=inputs,startup_inputs=','inputs=inputs.snapshot(),input_retention=inputs.stats(),startup_inputs=')
 marker='sky_capture=SkyCapture(d,rom.read_bytes()) if opt.capture_sky else None'
 assert source.count(marker)==1
 source=source.replace(marker,marker+'\n if sky_capture is not None:sky_capture.records=RecentRows(240)')
 source=source.replace('sky_capture_records=sky_capture.records if sky_capture is not None else [],','sky_capture_records=sky_capture.records.snapshot() if sky_capture is not None else [],sky_capture_retention=sky_capture.records.stats() if sky_capture is not None else None,')
 source=source.replace('producer_costs=[];simulation_costs=[]','producer_costs=ProducerRows();simulation_costs=DurationTotals()')
 source=source.replace('cost_summary(simulation_costs)','simulation_costs.stats()')
 source=source.replace("cost_summary([row['ns'] for row in producer_costs])",'producer_costs.duration.stats()')
 source=source.replace("{key:cost_summary([row['stages'].get(key,0) for row in producer_costs]) for key in sorted({key for row in producer_costs for key in row['stages']})}",'{key:value.stats() for key,value in producer_costs.stages.items()}')
 source=source.replace("world_preparation_stage_samples=getattr(worker.preparation_service,'stage_samples',[]),","world_preparation_stage_samples=getattr(worker.preparation_service,'stage_samples',[]),preparation_retention=getattr(worker.preparation_service,'preparation_retention',None),")
 source=source.replace('producer_cycle_samples=producer_costs,','producer_cycle_samples=producer_costs.snapshot(),producer_retention=producer_costs.stats(),')
 source=source.replace('from owned_sky_frame import attach_sky','from owned_sky_frame_reuse_candidate import attach_sky')
 assert source.count('sky_frame=attach_sky(C.string_at(frame,size.value),scene)')==1
 source=source.replace('sky_frame=attach_sky(C.string_at(frame,size.value),scene)','sky_frame=attach_sky(adapted if type(adapted) is bytes and len(adapted)==size.value else C.string_at(frame,size.value),scene)')
 source=source.replace('size=C.c_size_t();frame_read_boundaries=[]','size=C.c_size_t();frame_read_boundaries=[];captured_frame=None')
 old='result=capture_boundary_library.nf_original_frame_read_batch(C.cast(d.nf_native_owned_frame_read,C.c_void_p),epoch,candidate,frame,len(frame),C.byref(size),boundary)'
 assert source.count(old)==1
 source=source.replace(old,"from _owned_frame_capture_profile_candidate import capture as capture_immutable\n   captured_frame=capture_immutable(C.cast(d.nf_native_owned_frame_read,C.c_void_p).value,epoch,candidate);size.value=len(captured_frame);result=1")
 source=source.replace('owned_frame=C.string_at(frame,size.value) if opt.graph_snapshots or opt.regenerate_walls else None','owned_frame=(captured_frame if captured_frame is not None else C.string_at(frame,size.value)) if opt.graph_snapshots or opt.regenerate_walls else None')
 source=source.replace("assert C.string_at(legacy,size.value)==C.string_at(frame,size.value),'Batched complete frame differs'","assert C.string_at(legacy,size.value)==(captured_frame if captured_frame is not None else C.string_at(frame,size.value)),'Immutable complete frame differs'")
 source=source.replace('else frame,size.value,scene=scene)','else (captured_frame if captured_frame is not None and not opt.regenerate_walls else frame),size.value,scene=scene)')
 source=source.replace('report=dict(handoff_pool_stats=', 'report=dict(native_compare_releases_gil=True,private_immutable_capture_enabled=opt.native_capture_batch,handoff_pool_stats=')
 source=source.replace('batch=True,query=False,started_ns=started,completed_ns=time.perf_counter_ns(),native=list(boundary)','batch=True,private_immutable=True,query=False,started_ns=started,completed_ns=time.perf_counter_ns(),native=list(__import__("_owned_frame_capture_profile_candidate").last_profile())')
 source=source.replace('report=dict(',"report=dict(hud_lease_cleanup=getattr(worker,'hud_lease_cleanup',None),")
 source=source.replace("report=dict(","report=dict(background_copy_shutdown=getattr(worker,'copy_shutdown',None),")
 source=source.replace("viewport-sky-capture-probe.dll","viewport-sky-private-capture-probe.dll").replace("d.nf_native_owned_frame_read","d.nf_native_owned_frame_read_private")
 exec(compile(source,str(path),'exec'),dict(__name__='__main__',__file__=str(path),progress=progress,diagnostic_stats=diagnostic_stats,RecentRows=RecentRows,DurationTotals=DurationTotals,ProducerRows=ProducerRows,ProducerDeadlineRows=ProducerDeadlineRows))

















