"""Persistent sequential source-history stream; experimental worker protocol."""
def worker(connection,rom):
 import struct,math,os,time
 if os.environ.get('NFSUG_SHARED_INPUT_READ_TRACE')=='1':
  from owned_progressive_shared_transport_candidate import SharedInputConnection
  SharedInputConnection.input_read_trace=True
 native_portal_parent_batch=None
 if os.environ.get('NFSUG_NATIVE_PORTAL_PARENT_BATCH')=='1':import owned_portal_parent_batch_install as native_portal_parent_batch
 native_range_memory=None
 if os.environ.get('NFSUG_NATIVE_SCENE_RANGES')=='1':
  if any(os.environ.get(k)=='1' for k in ('NFSUG_SCENE_MERGE_CANDIDATE','NFSUG_MEMORY_SKIP_EMPTY_EXTEND')):raise ValueError('Conflicting scene memory candidates')
  import owned_native_range_memory_install_candidate as native_range_memory
 topology_reuse=os.environ.get('NFSUG_PORTAL_TOPOLOGY_REUSE')=='1'
 if topology_reuse:
  from owned_motion_visibility import PortalMotionPair
  PortalMotionPair.cache_topology=True
 memory_skip_empty=None
 if os.environ.get('NFSUG_MEMORY_SKIP_EMPTY_EXTEND')=='1':import owned_memory_skip_empty_install_candidate as memory_skip_empty
 memory_cpu_profile=None
 if os.environ.get('NFSUG_SCENE_MEMORY_CPU_PROFILE')=='1':import owned_scene_memory_cpu_profile_candidate as memory_cpu_profile
 wall_source_index=None
 if os.environ.get('NFSUG_WALL_SOURCE_INDEX')=='1':import owned_wall_source_index_install_candidate as wall_source_index
 scene_merge=None
 if os.environ.get('NFSUG_SCENE_MERGE_CANDIDATE')=='1':import owned_scene_merge_install_candidate as scene_merge
 model_record_reuse=None
 endpoint_validation_reuse=None
 if os.environ.get('NFSUG_ENDPOINT_VALIDATION_REUSE')=='1':
  if os.environ.get('NFSUG_GRAPH_FRAME_MATCH_CACHE')=='1':raise ValueError('Conflicting graph validation caches')
  import owned_endpoint_validation_reuse_candidate as endpoint_validation_reuse
  endpoint_validation_reuse.install()
 graph_match_cache=None
 if os.environ.get('NFSUG_GRAPH_FRAME_MATCH_CACHE')=='1':
  import owned_graph_frame_match_cache_install_candidate as graph_match_cache
 offset_cache=None
 if os.environ.get('NFSUG_WALL_OFFSET_PAIR_CACHE')=='1':
  import owned_sampled_graph_wall_visibility as wall_selection
  import owned_sampled_graph_wall_visibility_offset_cache_candidate as offset_cache
  wall_selection.selected_graph_walls=offset_cache.selected_graph_walls
 # Match the verified live child preparation helpers before importing sampler code.
 import owned_wall_record_reuse_install_candidate
 import owned_rom_slice_reuse_install_candidate
 import owned_record_miss_container_reuse_install_candidate
 lazy_wall_textures=None
 if os.environ.get('NFSUG_LAZY_WALL_TEXTURES')=='1':
  import owned_wall_lazy_texture_candidate as lazy_wall_textures
  lazy_wall_textures.install()
 small_model_blocks=None
 if os.environ.get('NFSUG_MODEL_SMALL_BLOCK_BYTES')=='1':
  import owned_model_small_block_bytes_candidate as small_model_blocks
  small_model_blocks.install()
 if os.environ.get("NFSUG_ROAD_CONSTRUCTOR_TRACE")=="1":import owned_road_constructor_trace_install_candidate
 lazy_road_records=None
 if os.environ.get("NFSUG_VALIDATED_LAZY_ROAD_RECORDS")=="1":
  if os.environ.get("NFSUG_ROAD_CONSTRUCTOR_TRACE")=="1":raise ValueError("Conflicting constructor trace/lazy records")
  import owned_lazy_road_records_install_candidate as lazy_road_records
  lazy_road_records.install()
 road_transaction=None
 if os.environ.get("NFSUG_CAMERA_CLIP_TRANSACTION")=="1":
  if os.environ.get("NFSUG_ROAD_NATIVE_CALL_TRACE")=="1":raise ValueError("Conflicting road call diagnostics/transaction")
  import owned_camera_clip_transaction_install_candidate as road_transaction
  road_transaction.install()
 narrow_metadata=None
 if os.environ.get('NFSUG_PREFIX_MODEL_METADATA')=='1':
  if os.environ.get('NFSUG_NARROW_SAMPLE_MODEL_METADATA')=='1':raise ValueError('Conflicting metadata candidates')
  import owned_prefix_model_metadata_install_candidate as narrow_metadata
  narrow_metadata.install()
 elif os.environ.get('NFSUG_NARROW_SAMPLE_MODEL_METADATA')=='1':
  import owned_sample_model_metadata_install_candidate as narrow_metadata
  narrow_metadata.install()
 if os.environ.get('NFSUG_MODEL_RECORD_MISS_REUSE')=='1':import owned_model_record_miss_reuse_install_candidate as model_record_reuse
 import owned_road_planner_library_install_candidate
 import owned_road_material_decode_install_candidate
 import owned_preparation_fixed_types_install_candidate
 spatial_decode_cache=None
 if os.environ.get('NFSUG_CHILD_SPATIAL_DECODE_CACHE')=='1':
  import owned_spatial_decode_cache_candidate as spatial_decode_cache
  spatial_decode_cache.install()
 visibility_library_reuse=os.environ.get('NFSUG_CHILD_VISIBILITY_LIBRARY_REUSE')=='1'
 if visibility_library_reuse:import owned_visibility_thread_library_install_candidate
 portal_point_cache_candidate=os.environ.get('NFSUG_PORTAL_POINT_CACHE')=='1'
 if portal_point_cache_candidate:import owned_portal_point_cache_install_candidate
 road_flat_join_candidate=os.environ.get('NFSUG_ROAD_FLAT_JOIN')=='1'
 if road_flat_join_candidate:import owned_road_encode_flat_join_install_candidate
 road_single_join_candidate=os.environ.get('NFSUG_ROAD_SINGLE_JOIN')=='1'
 if road_single_join_candidate:import owned_road_single_join_install_candidate
 road_record_candidate=os.environ.get("NFSUG_ROAD_RECORD_CONSTRUCTION")=="1"
 if road_record_candidate:import owned_road_record_worker_install_candidate
 road_material_resolution=None
 if os.environ.get('NFSUG_ROAD_MATERIAL_RESOLUTION')=='1':
  import owned_road_material_resolution_install_candidate as road_material_resolution
  road_material_resolution.install()
 corrected_road_pair=None
 if os.environ.get('NFSUG_CORRECTED_ROAD_PAIR')=='1':import owned_corrected_road_pair_install as corrected_road_pair
 portal_depth_candidate=os.environ.get("NFSUG_PORTAL_DEPTH_PROJECTION")=="1"
 if portal_depth_candidate:
  import owned_portal_continuous as portal_arithmetic
  from owned_portal_depth_projection_candidate import edge as depth_edge
  portal_arithmetic.edge.__code__=depth_edge.__code__
 import owned_endpoint_road_planner as planner
 from owned_endpoint_road_fixed_types_candidate import endpoint_road_span_candidates
 planner.endpoint_road_span_candidates=endpoint_road_span_candidates
 import owned_source_presentation_batch_candidate as batch
 from owned_source_depth_transition_candidate import SourceFaceDeterminants
 batch.SourceFaceDeterminants=SourceFaceDeterminants
 from pathlib import Path
 from owned_scene_process_transport import unpack
 from owned_endpoint_road_planner import EndpointRoadPlanner
 from owned_prepared_world_segmented_candidate import PreparedWorldMotion
 if os.environ.get('NFSUG_MODEL_VISIT_INDEX')=='1':
  import owned_model_visit_index_install_candidate
 frame_prefix_cache=None
 if os.environ.get('NFSUG_FRAME_PREFIX_CACHE')=='1':
  import owned_frame_prefix_cache_candidate as frame_prefix_cache
  frame_prefix_cache.install()
 wall_capture=None
 if os.environ.get('NFSUG_UPSTREAM_WALL_CAPTURE')=='1':
  import owned_upstream_wall_capture_candidate as wall_capture
  wall_capture.install()
 census=None
 if os.environ.get('NFSUG_CHILD_OBJECT_CENSUS')=='1':import owned_child_object_census_candidate as census
 two_entry_memory=None
 if os.environ.get('NFSUG_SCENE_MEMORY_TWO_ENTRY')=='1':
  import scene_memory_two_entry_candidate as two_entry_memory
  two_entry_memory.install()
 if os.environ.get('NFSUG_CHILD_SCENE_MEMORY_TRACE')=='1':
  import child_scene_memory_trace_candidate
  child_scene_memory_trace_candidate.install()
 child_gc_lease=None
 mask_stage_trace=None
 if os.environ.get('NFSUG_SOURCE_MASK_STAGE_TRACE')=='1':import owned_source_mask_stage_trace as mask_stage_trace
 projection_call_trace=None
 if os.environ.get('NFSUG_SOURCE_PROJECTION_CALL_TRACE')=='1':import owned_source_projection_call_trace as projection_call_trace
 gc_trace=None
 if os.environ.get('NFSUG_CHILD_GC_TRACE')=='1':import owned_child_gc_trace_candidate as gc_trace
 from owned_progressive_source_samples_candidate import ProgressiveSourceWorldSamples
 endpoint_plan_records=None
 if os.environ.get('NFSUG_SOURCE_ENDPOINT_PLAN_RECORDS')=='1':
  from owned_source_endpoint_plan_records_candidate import install
  endpoint_plan_records=install()
 from owned_progressive_frame_codec_candidate import FrameEncoder
 table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);history=roads=previous=generation=None
 def clear():
  nonlocal history,roads,previous
  if history is not None:history.close()
  history=roads=previous=None
  if spatial_decode_cache is not None:spatial_decode_cache._local.entries=[]
 handoff_trace=os.environ.get('NFSUG_CHILD_REQUEST_HANDOFF_TRACE')=='1'
 last_terminal_send_end=last_idle_cleanup_end=None
 try:
  while True:
   recv_begin=time.perf_counter_ns() if handoff_trace else None
   request=connection.recv()
   recv_end=time.perf_counter_ns() if handoff_trace else None
   request_handoff_profile=None if not handoff_trace else dict(previous_terminal_send_end_ns=last_terminal_send_end,previous_idle_cleanup_end_ns=last_idle_cleanup_end,recv_begin_ns=recv_begin,recv_end_ns=recv_end)
   if request is None:break
   if isinstance(request,tuple) and request[0]=='warm':
    _,requested,packet=request;began=time.perf_counter_ns()
    try:
     if type(requested) is not int or requested<0 or history is not None:raise ValueError('Invalid progressive startup')
     frame,scene=unpack(packet,rom);scene.match(frame)
     from sample_owned_motion import rigid_library
     from owned_wall_visibility_candidate import helper
     from owned_transition_readiness import prepare as transition_readiness
     rigid_library();helper();ready=transition_readiness()
     history=EndpointRoadPlanner(rom,table);roads,_=history.plan(scene.graph);generation=requested;previous=(frame,scene)
     startup_gc=None
     if os.environ.get('NFSUG_CHILD_STARTUP_GC')=='1':
      import gc
      gc_begin=time.perf_counter_ns();gc_collected=gc.collect();startup_gc=dict(collected=gc_collected,elapsed_ns=time.perf_counter_ns()-gc_begin,enabled=gc.isenabled())
     if (os.environ.get('NFSUG_CHILD_GC_INTERVAL')=='1' or os.environ.get('NFSUG_CHILD_GC_OBSERVER')=='1') and child_gc_lease is None:
      from owned_startup_gc_scan_lease_candidate import StartupGCScanLease
      child_gc_lease=StartupGCScanLease()
      import gc
      child_gc_lease.enter(50 if os.environ.get('NFSUG_CHILD_GC_INTERVAL')=='1' else gc.get_threshold()[2])
     connection.send(('warm',requested,dict(child_gc_interval_selected=os.environ.get('NFSUG_CHILD_GC_INTERVAL')=='1',child_gc_observer_selected=child_gc_lease is not None,startup_gc=startup_gc,epoch=scene.graph.epoch,refresh=scene.graph.refresh,transition_readiness=ready,worker_process=os.getpid(),wall_ns=time.perf_counter_ns()-began)))
    except BaseException as e:
     clear();connection.send(('warm_error',requested,repr(e)))
    continue
   began=time.perf_counter_ns();constructed=None;decoded=initialized=None;sample_rows=[];last_ack=None
   cpu_trace=os.environ.get("NFSUG_PROGRESSIVE_CPU_TRACE")=="1";began_cpu=time.thread_time_ns() if cpu_trace else None;decoded_cpu=initialized_cpu=constructed_cpu=last_ack_cpu=None
   prepared=samples=None;count=0;status='complete';error=None;requested=-1;reused=False;fine_trace=False
   cycle_trace=os.environ.get('NFSUG_PROGRESSIVE_CYCLE_TRACE')=='1';initialized_cycles=constructed_cycles=last_ack_cycles=None
   if cycle_trace:
    from owned_thread_cycles import read as cycle_read
    import threading
    cycle_thread=threading.get_native_id()
   else:cycle_read=None;cycle_thread=None
   try:
    requested,older,identity,newer,alphas=request[:5]
    seeded=len(request)==6 and request[5] is True
    if len(request) not in (5,6) or (len(request)==6 and not seeded):raise ValueError("Invalid endpoint reference capability")
    if type(requested) is not int or requested<0 or (generation is not None and requested<generation):raise ValueError('Invalid request generation')
    if not 0<=len(alphas)<=8 or len(set(alphas))!=len(alphas) or any(not math.isfinite(a) or not 0<a<1 for a in alphas):raise ValueError('Invalid source sample list')
    if generation!=requested:clear();generation=requested
    if older is None:
     if previous is None or previous[1].identity!=identity:raise ValueError('Unowned retained source scene')
     a,sa=previous;reused=True
    else:a,sa=unpack(older,rom)
    if sa.identity!=identity:raise ValueError('Older source identity mismatch')
    fine_first=int(os.environ.get("NFSUG_PROGRESSIVE_FINE_FIRST","0"));fine_last=int(os.environ.get("NFSUG_PROGRESSIVE_FINE_LAST","4294967295"))
    if fine_first>fine_last:raise ValueError("Invalid fine trace range")
    fine_trace=os.environ.get("NFSUG_PROGRESSIVE_FINE_TRACE")=="1" and fine_first<=identity[1]<=fine_last
    if os.environ.get("NFSUG_SLOW_REQUEST_TRACE")=="1":fine_trace=True
    b,sb=unpack(newer,rom)
    decoded=time.perf_counter_ns();decoded_cpu=time.thread_time_ns() if cpu_trace else None
    if history is None:history=EndpointRoadPlanner(rom,table);roads,_=history.plan(sa.graph)
    elif history.epoch!=sa.graph.epoch or history.refresh!=sa.graph.refresh:raise ValueError('Source history out of order')
    initialized=time.perf_counter_ns();initialized_cpu=time.thread_time_ns() if cpu_trace else None;initialized_cycles=cycle_read() if cycle_trace else None
    if os.environ.get('NFSUG_CHILD_SCENE_CAPTURE_REFRESH'):
     from owned_child_scene_capture_candidate import capture
     capture((a,sa),(b,sb),alphas,history,roads)
    prepared=PreparedWorldMotion(a,b,sa,sb,history,roads,rom);advanced=prepared.take_next_history();history.close();history=advanced;roads=prepared.endpoint_roads[1]
    constructed=time.perf_counter_ns();last_ack=constructed;constructed_cpu=time.thread_time_ns() if cpu_trace else None;last_ack_cpu=constructed_cpu;constructed_cycles=cycle_read() if cycle_trace else None;last_ack_cycles=constructed_cycles
    encoder=FrameEncoder(requested,owners=(a,b) if seeded else ())
    def publish(packet):
     nonlocal count,status,last_ack,last_ack_cpu,last_ack_cycles
     ready=time.perf_counter_ns();ready_cpu=time.thread_time_ns() if cpu_trace else None;ready_cycles=cycle_read() if cycle_trace else None;index=count;packet=(packet[0],encoder.encode(packet[1]),*packet[2:]);encoded=time.perf_counter_ns();connection.send(('sample',requested,index,packet));sent=time.perf_counter_ns();count+=1
     if not connection.poll(15):raise TimeoutError('Sample acknowledgement timeout')
     ack=connection.recv();acked=time.perf_counter_ns()
     sample_rows.append(dict(index=index,ready_ns=ready,encode_ns=encoded-ready,send_ns=sent-encoded,ack_wait_ns=acked-sent,prepare_since_ack_ns=ready-last_ack,prepare_cpu_ns=None if not cpu_trace else ready_cpu-last_ack_cpu,prepare_thread_cycles=None if not cycle_trace else ready_cycles-last_ack_cycles,shared_write=getattr(getattr(connection,"connection",None),"last_write_profile",None)));last_ack=acked;last_ack_cpu=time.thread_time_ns() if cpu_trace else None;last_ack_cycles=cycle_read() if cycle_trace else None
     if ack==('retire',requested):status='retired';raise RuntimeError('Stream retired')
     if ack!=('ack',requested,index):raise ValueError('Invalid sample acknowledgement')
    if alphas:samples=ProgressiveSourceWorldSamples(prepared,alphas,trace=fine_trace,on_sample=publish)
    previous=(b,sb)
   except BaseException as e:
    if status!='retired':status='error';error=repr(e)
    clear()
   finally:
    if narrow_metadata is not None:narrow_metadata.clear()
    if samples is not None:samples.close()
    if prepared is not None:prepared.close()
    if endpoint_validation_reuse is not None:endpoint_validation_reuse.clear()
   slow_request_trace=None
   if os.environ.get("NFSUG_SLOW_REQUEST_TRACE")=="1":
    from owned_slow_request_trace_candidate import retain
    slow_request_trace=retain(prepared,samples,sample_rows,began)
   connection.send(('terminal',requested,status,count,error,dict(scene_memory_two_entry_stats=None if two_entry_memory is None else dict(two_entry_memory.stats),corrected_road_pair_stats=None if corrected_road_pair is None else dict(corrected_road_pair.stats),native_portal_parent_batch_stats=None if native_portal_parent_batch is None else dict(native_portal_parent_batch.stats),lazy_road_record_stats=None if lazy_road_records is None else dict(lazy_road_records.stats),road_transaction_stats=None if road_transaction is None else dict(road_transaction.stats),slow_request_trace=slow_request_trace,narrow_model_metadata_stats=None if narrow_metadata is None else dict(narrow_metadata.stats),narrow_model_metadata_retained_entries=None if narrow_metadata is None else len(getattr(narrow_metadata.local,"entries",())),request_handoff_profile=request_handoff_profile,endpoint_validation_reuse_stats=None if endpoint_validation_reuse is None else dict(endpoint_validation_reuse.stats),endpoint_validation_retained_entries=None if endpoint_validation_reuse is None else len(getattr(endpoint_validation_reuse.local,"entries",[])),lazy_wall_texture_stats=None if lazy_wall_textures is None else dict(lazy_wall_textures.stats),small_model_block_stats=None if small_model_blocks is None else dict(small_model_blocks.stats),native_range_memory_stats=None if native_range_memory is None else dict(native_range_memory.stats),portal_topology_reuse_selected=topology_reuse,source_mask_stage_trace=None if mask_stage_trace is None else mask_stage_trace.snapshot(),source_projection_call_trace=None if projection_call_trace is None else projection_call_trace.snapshot(),memory_skip_empty_extend_stats=None if memory_skip_empty is None else dict(memory_skip_empty.stats),wall_source_index_stats=None if wall_source_index is None else dict(wall_source_index.stats),scene_merge_stats=None if scene_merge is None else dict(scene_merge.stats),model_record_miss_reuse_selected=model_record_reuse is not None,graph_frame_match_cache_stats=None if graph_match_cache is None else dict(graph_match_cache.stats),wall_offset_pair_cache_stats=None if offset_cache is None else dict(offset_cache.stats),child_object_census=None if census is None else census.snapshot(),child_idle_release_enabled=os.environ.get('NFSUG_CHILD_RELEASE_IDLE')=='1',child_gc_trace=None if gc_trace is None else gc_trace.snapshot(began,time.perf_counter_ns()),road_material_resolution_stats=None if road_material_resolution is None else dict(road_material_resolution.stats),portal_point_cache_candidate=portal_point_cache_candidate,road_flat_join_candidate=road_flat_join_candidate,road_single_join_candidate=road_single_join_candidate,visibility_library_reuse_selected=visibility_library_reuse,spatial_decode_cache_selected=spatial_decode_cache is not None,spatial_decode_cache_entries=0 if spatial_decode_cache is None else len(getattr(spatial_decode_cache._local,"entries",[])),portal_depth_candidate=portal_depth_candidate,road_record_candidate=road_record_candidate,pid=os.getpid(),input_reused=reused,history_identity=None if history is None else (history.epoch,history.refresh),clean_request_close=True,cycle_trace=cycle_trace,cycle_thread=cycle_thread,world_construct_thread_cycles=None if not cycle_trace or constructed_cycles is None or initialized_cycles is None else constructed_cycles-initialized_cycles,cpu_trace=cpu_trace,fine_trace=fine_trace,model_visit_callable=None if not (fine_trace or os.environ.get('NFSUG_MODEL_VISIT_SELECTION_TRACE')=='1') else dict(module=__import__('owned_sampled_world_segmented_candidate').sampled_model_visit.__module__,filename=__import__('owned_sampled_world_segmented_candidate').sampled_model_visit.__code__.co_filename,name=__import__('owned_sampled_world_segmented_candidate').sampled_model_visit.__qualname__),frame_prefix_cache_stats=None if frame_prefix_cache is None else dict(frame_prefix_cache.stats),child_started_cpu_ns=began_cpu,decoded_cpu_ns=decoded_cpu,initialized_cpu_ns=initialized_cpu,constructed_cpu_ns=constructed_cpu,input_read_profile=getattr(connection,'last_read_profile',None),child_started_ns=began,constructed_ns=constructed,child_finished_ns=time.perf_counter_ns(),sample_transfer_rows=sample_rows,construct_stages=list(getattr(prepared,"construct_stages",[])) if fine_trace else [],decoded_ns=decoded,initialized_ns=initialized,source_setup_stages=[] if samples is None else samples.source_setup_stages,sample_timings=[] if samples is None else samples.sample_timings)))
   if handoff_trace:last_terminal_send_end=time.perf_counter_ns()
   # Terminal serialization and every sample acknowledgement have completed.
   # Keep only previous/latest scene and advanced road history across idle waits.
   if os.environ.get('NFSUG_CHILD_RELEASE_IDLE')=='1':
    prepared=samples=encoder=None
    request=older=newer=a=sa=b=sb=publish=None
   if handoff_trace:last_idle_cleanup_end=time.perf_counter_ns()
 finally:
  try:
   if wall_capture is not None:wall_capture.save()
  finally:
   try:
    clear()
    if child_gc_lease is not None:
     child_gc_lease.close()
     import json
     Path('work/camera/prototype-runs/child-gc-interval-'+str(os.getpid())+'.json').write_text(json.dumps(child_gc_lease.evidence,indent=2))
   finally:
    if memory_cpu_profile is not None:memory_cpu_profile.save()
    connection.close()






