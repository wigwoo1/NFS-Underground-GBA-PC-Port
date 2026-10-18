from owned_double_array_type import double_array_type
"""Sequential child-owned road history with bounded parent preparation futures."""
import ctypes as C,multiprocessing as mp,struct,time,math,pickle,os
from pathlib import Path
from owned_thread_cycles import read as thread_cycles
from owned_preparation_pipeline import PreparationPipeline
from owned_scene_process_transport import pack,unpack

def encode_samples(samples,trace=None,borrow_tails=False):
 tails=[];encoded=[];original_bytes=0
 for alpha,value in samples.items():
  if trace is not None:started=time.perf_counter_ns();cycles=thread_cycles()
  frame=value[0];end=40+struct.unpack_from('<I',frame,8)[0]
  if end>len(frame):raise ValueError('Invalid process geometry length')
  # Check an existing exact suffix before allocating another multi-MB copy.
  index=next((i for i,t in enumerate(tails) if len(t)==len(frame)-end and frame.endswith(t)),None)
  if index is None:
   index=len(tails)
   if borrow_tails:
    if type(frame) is not bytes:raise ValueError("Borrowed process tail requires immutable frame bytes")
    tails.append(memoryview(frame)[end:])
   else:tails.append(frame[end:])
  arrays=tuple(None if x is None else bytes(x) for x in value[1:4])
  original_bytes+=len(frame)+sum(len(x) for x in arrays if x is not None)
  encoded.append((alpha,(frame[:end],index,*arrays,value[4])))
  if trace is not None:trace.append(dict(alpha=alpha,started_ns=started,completed_ns=time.perf_counter_ns(),thread_cycles=thread_cycles()-cycles,frame_bytes=len(frame),tail_index=index))
 transferred_bytes=sum(map(len,tails))+sum(len(v[0])+sum(len(x) for x in v[2:5] if x is not None) for _,v in encoded)
 return dict(tails=tails,samples=encoded,original_bytes=original_bytes,transferred_bytes=transferred_bytes)

def _child(connection,rom,shared_output=None):
 from owned_endpoint_road_planner import EndpointRoadPlanner
 from owned_prepared_world_motion import PreparedWorldMotion
 from owned_precomputed_world_samples import PrecomputedWorldSamples
 native_frame_join_enabled=os.environ.get("NF_PROCESS_NATIVE_FRAME_JOIN")=="1"
 if native_frame_join_enabled:
  import owned_sampled_world_frame as assembly
  from owned_native_frame_join import join_frame,trace
  assembly.join_frame=join_frame;assembly.join_frame_trace=trace
 from owned_gc_trace import CollectionTrace
 child_gc=CollectionTrace()
 priority=None
 if os.environ.get("NF_PREPARATION_BELOW_NORMAL")=="1":
  k=C.WinDLL("kernel32",use_last_error=True)
  k.GetCurrentProcess.restype=C.c_void_p
  k.GetPriorityClass.argtypes=[C.c_void_p];k.GetPriorityClass.restype=C.c_uint32
  k.SetPriorityClass.argtypes=[C.c_void_p,C.c_uint32];k.SetPriorityClass.restype=C.c_int
  handle=k.GetCurrentProcess();before=k.GetPriorityClass(handle)
  if not k.SetPriorityClass(handle,0x4000):raise C.WinError(C.get_last_error())
  after=k.GetPriorityClass(handle)
  if after!=0x4000:raise RuntimeError("Preparation process priority mismatch")
  priority=dict(before=before,requested=0x4000,observed=after,process=mp.current_process().pid)
 shared_memory=None;shared_serial=0
 if shared_output is not None:
  from multiprocessing.shared_memory import SharedMemory
  shared_memory=SharedMemory(name=shared_output[0])
 table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);history=None;roads=None;generation=None;previous=None
 try:
  while True:
   request=connection.recv()
   if request is None:break
   if isinstance(request,tuple) and request[0]=='warm':
    _,requested_generation,packet,*warm_options=request
    prewarm_scenery_builder=bool(warm_options and warm_options[0])
    began=time.perf_counter_ns()
    try:
     frame,scene=unpack(packet,rom);scene.match(frame)
     if history is not None:raise ValueError('Process startup history already initialized')
     builder_prewarm=None
     if prewarm_scenery_builder:
      import owned_scenery_record_pairs
      _,cache_hit=owned_scenery_record_pairs._record_builder_for_rom(rom)
      builder_prewarm=dict(worker_process=mp.current_process().pid,cache_hit=cache_hit)
     from sample_owned_motion import rigid_library
     from owned_wall_visibility_candidate import helper
     rigid_library();helper()
     from owned_transition_readiness import prepare as transition_readiness
     transitions_ready=transition_readiness()
     history=EndpointRoadPlanner(rom,table);roads,_=history.plan(scene.graph);generation=requested_generation;previous=(frame,scene)
     connection.send(('warm',dict(transition_readiness=transitions_ready,model_record_builder_prewarm=builder_prewarm,epoch=scene.graph.epoch,refresh=scene.graph.refresh,worker_process=mp.current_process().pid,wall_ns=time.perf_counter_ns()-began),0))
    except BaseException as error:connection.send(('error',repr(error),0))
    continue
   requested_generation,older,older_identity,newer,alphas=request
   prepared=None
   try:
    started=time.perf_counter_ns();cpu_start=time.thread_time_ns();gc_begin=len(child_gc.rows)
    if older is None:
     if previous is None or generation!=requested_generation or previous[1].identity!=older_identity:raise ValueError('Unowned retained process scene')
     a,sa=previous
    else:a,sa=unpack(older,rom)
    if sa.identity!=older_identity:raise ValueError('Process older identity mismatch')
    b,sb=unpack(newer,rom)
    decoded=time.perf_counter_ns()
    if history is None or generation!=requested_generation or history.epoch!=sa.graph.epoch or history.refresh!=sa.graph.refresh:
     if history is not None:history.close()
     history=EndpointRoadPlanner(rom,table);roads,_=history.plan(sa.graph);generation=requested_generation
    initialized=time.perf_counter_ns()
    prepared=PreparedWorldMotion(a,b,sa,sb,history,roads,rom)
    construct_trace=prepared.construct_stages
    advanced=prepared.take_next_history();history.close();history=advanced;roads=prepared.endpoint_roads[1]
    constructed=time.perf_counter_ns();encode_trace=[];sample_trace=[];prepared_close_ns=None;encoding_cleanup=None
    if alphas:
     samples=PrecomputedWorldSamples(prepared,alphas,trace=True);prepared=None
     sampled=time.perf_counter_ns();sample_trace=samples.sample_timings;prepared_close_ns=samples.prepared_close_ns
     try:encoded=encode_samples(samples.samples,encode_trace,borrow_tails=shared_memory is not None)
     finally:
      close_begin=time.perf_counter_ns();close_cpu=time.thread_time_ns();close_cycles=thread_cycles()
      samples.close()
      encoding_cleanup=dict(close_begin_ns=close_begin,close_end_ns=time.perf_counter_ns(),close_cpu_ns=time.thread_time_ns()-close_cpu,close_thread_cycles=thread_cycles()-close_cycles)
    else:
     prepared.close();prepared=None
     sampled=time.perf_counter_ns()
     encoded=dict(history_only=True,tails=[],samples=[],original_bytes=0,transferred_bytes=0)
    replacement_begin=time.perf_counter_ns();replacement_cpu=time.thread_time_ns();replacement_cycles=thread_cycles()
    previous=(b,sb)
    encoded_at=time.perf_counter_ns()
    if encoding_cleanup is not None:encoding_cleanup.update(replacement_begin_ns=replacement_begin,replacement_end_ns=encoded_at,replacement_cpu_ns=time.thread_time_ns()-replacement_cpu,replacement_thread_cycles=thread_cycles()-replacement_cycles)
    shared_write=None
    if shared_memory is None:connection.send(('ok',encoded,encoded_at-started))
    else:
     from owned_shared_payload import write_payload
     shared_serial+=1
     write_begin=time.perf_counter_ns();write_cycles=thread_cycles()
     descriptor=write_payload(shared_memory,encoded,requested_generation,shared_serial)
     write_end=time.perf_counter_ns();write_end_cycles=thread_cycles()
     shared_write=dict(begin_ns=write_begin,end_ns=write_end,thread_cycles=write_end_cycles-write_cycles,payload_bytes=descriptor[3],deduplication_enabled=os.environ.get("NF_SHARED_DEDUP_BYTES")=="1")
     connection.send(('shared',descriptor,encoded_at-started))
     if not connection.poll(30) or connection.recv()!=('ack',descriptor):raise RuntimeError('Shared output acknowledgement failed')
    sent=time.perf_counter_ns()
    connection.send(dict(native_frame_join_enabled=native_frame_join_enabled,child_gc_observed=True,child_gc_rows=child_gc.rows[gc_begin:],child_gc_dropped=child_gc.dropped,encoding_cleanup=encoding_cleanup,shared_write=shared_write,child_boundaries=dict(started_ns=started,decoded_ns=decoded,initialized_ns=initialized,constructed_ns=constructed,sampled_ns=sampled,encoded_ns=encoded_at,sent_ns=sent),native_road_reader_enabled=os.environ.get('NF_NATIVE_ROAD_READER')=='1',construct_stages=construct_trace,sample_timings=sample_trace,prepared_close_ns=prepared_close_ns,encode_samples=encode_trace,prepared_sample_count=len(alphas),history_only=not bool(alphas),priority=priority,decode_ns=decoded-started,history_init_ns=initialized-decoded,construct_advance_ns=constructed-initialized,precompute_ns=sampled-constructed,encode_ns=encoded_at-sampled,send_ns=sent-encoded_at,child_thread_cpu_ns=time.thread_time_ns()-cpu_start))
   except BaseException as error:
    if prepared is not None:prepared.close()
    if history is not None:history.close();history=None
    previous=None
    connection.send(('error',repr(error),0))
 finally:
  child_gc.close()
  if history is not None:history.close()
  if shared_memory is not None:shared_memory.close()
  connection.close()

class ProcessSamples:
 def __init__(self,encoded):
  self.samples={};self.decode_stages=[];size=0
  self.history_only=False
  if 'history_only' in encoded:
   if encoded!=dict(history_only=True,tails=[],samples=[],original_bytes=0,transferred_bytes=0) or encoded['history_only'] is not True:raise ValueError('Invalid history-only process result')
   self.history_only=True
   return
  tails=encoded['tails'];encoded=encoded['samples']
  frame_cache={} if getattr(type(self),"reuse_immutable_frames",False) else None
  if not 1<=len(tails)<=8 or any(not isinstance(t,bytes) for t in tails):raise ValueError('Invalid process frame tails')
  if not 1<=len(encoded)<=8:raise ValueError('Invalid process sample count')
  for alpha,value in encoded:
   if not math.isfinite(alpha) or not 0<=alpha<=1 or alpha in self.samples:raise ValueError('Invalid process sample alpha')
   prefix,index,camera,models,bounds,detail=value;arrays=[]
   if not isinstance(index,int) or not 0<=index<len(tails):raise ValueError('Invalid process tail reference')
   if len(prefix)<40 or 40+struct.unpack_from('<I',prefix,8)[0]!=len(prefix):raise ValueError('Invalid process geometry prefix')
   started=time.perf_counter_ns();cycles=thread_cycles()
   key=(prefix,index)
   reused=frame_cache is not None and key in frame_cache
   if reused:frame=frame_cache[key]
   else:
    frame=prefix+tails[index]
    if frame_cache is not None:frame_cache[key]=frame
   completed=time.perf_counter_ns();end_cycles=thread_cycles()
   self.decode_stages.append(dict(alpha=alpha,name="frame_join",immutable_frame_reused=reused,started_ns=started,completed_ns=completed,wall_ns=completed-started,thread_cycles=end_cycles-cycles,bytes=len(frame)))
   size+=len(frame)
   array_start=time.perf_counter_ns();array_cycles=thread_cycles()
   for raw in (camera,models,bounds):
    if raw is None:arrays.append(None);continue
    if len(raw)%8:raise ValueError('Invalid process double array')
    size+=len(raw);arrays.append(double_array_type(len(raw)//8).from_buffer_copy(raw))
   array_end=time.perf_counter_ns();array_end_cycles=thread_cycles()
   self.decode_stages.append(dict(alpha=alpha,name='array_decode',started_ns=array_start,completed_ns=array_end,wall_ns=array_end-array_start,thread_cycles=array_end_cycles-array_cycles))
   if size>64*1024*1024:raise ValueError('Process output budget exceeded')
   self.samples[alpha]=(frame,*arrays,detail)
 def sample(self,alpha):
  if alpha not in self.samples:raise ValueError('Unprepared process sample')
  return self.samples[alpha]
 def close(self):self.samples.clear()

class ProcessPreparationService:
 supports_pending_replay=True
 def __init__(self,rom,capacity,shared_output=False):
  from owned_shared_blob import SharedBlobOwner
  self.shared_serial=0
  self.shared_owner=SharedBlobOwner(64*1024*1024) if shared_output else None
  shared_descriptor=(self.shared_owner.memory.name,self.shared_owner.capacity) if self.shared_owner else None
  context=mp.get_context('spawn');self.connection,child=context.Pipe();self.process=context.Process(target=_child,args=(child,rom,shared_descriptor),daemon=True);self.process.start();child.close()
  self.previous=None;self.previous_generation=None;self.failed=False;self.pipeline=PreparationPipeline(capacity);self.stage_samples=[];self.profiles=[];self.profile_refresh=None
 def warm_start(self,frame,scene):
  scene.match(frame);generation=self.pipeline.generation
  class Ready:
   def __init__(self,evidence):self.evidence=evidence
   def close(self):pass
  def initialize():
   if self.failed or not self.process.is_alive():raise RuntimeError('Preparation child unavailable')
   prewarm_builder=bool(getattr(self,'prewarm_scenery_builder',False) or os.environ.get('NF_PREWARM_SCENERY_RECORD_BUILDER')=='1')
   self.connection.send(('warm',generation,pack(frame,scene),prewarm_builder))
   if not self.connection.poll(30):self.failed=True;raise RuntimeError('Process startup response stalled')
   status,evidence,_=self.connection.recv()
   if status!='warm':self.failed=True;raise RuntimeError('Process startup: '+str(evidence))
   if (evidence['epoch'],evidence['refresh'])!=(scene.graph.epoch,scene.graph.refresh):self.failed=True;raise ValueError('Process startup identity mismatch')
   return Ready(evidence)
  return self.pipeline.take(self.pipeline.submit(initialize,timeout=30)).evidence
 def submit(self,older,newer,alphas=None,timeout=0,abort=None):
  if alphas is None:raise ValueError('Process preparation requires complete precomputed samples')
  generation=self.pipeline.generation
  def prepare():
   started=time.perf_counter_ns()
   if self.failed or not self.process.is_alive():raise RuntimeError('Preparation child unavailable')
   reuse=self.previous is older and self.previous_generation==generation
   old_packet=None if reuse else pack(*older);new_packet=pack(*newer)
   input_bytes=sum(len(x) for packet in (old_packet,new_packet) if packet is not None for x in packet if x is not None)
   request=(generation,old_packet,older[1].identity,new_packet,tuple(alphas))
   self.connection.send(request)
   if not self.connection.poll(30):
    self.failed=True;raise RuntimeError('Preparation child response stalled')
   status,payload,elapsed=self.connection.recv()
   shared_read=None
   if status=='shared':
    from owned_shared_payload import read_payload
    descriptor=payload
    if self.shared_owner is None or descriptor[0]!=self.shared_owner.memory.name or descriptor[2]!=self.shared_serial+1:
     self.failed=True;raise RuntimeError('Unexpected shared output owner or serial')
    read_begin=time.perf_counter_ns();read_cycles=thread_cycles()
    try:payload=read_payload(descriptor,generation,self.shared_owner.memory)
    except BaseException:self.failed=True;raise
    read_end=time.perf_counter_ns();read_end_cycles=thread_cycles()
    shared_read=dict(begin_ns=read_begin,end_ns=read_end,thread_cycles=read_end_cycles-read_cycles,payload_bytes=descriptor[3])
    self.shared_serial=descriptor[2];self.connection.send(('ack',descriptor));status='ok'
   if status!='ok':
    self.previous=None;raise RuntimeError('Preparation child: '+payload)
   child_stages=self.connection.recv()
   received=time.perf_counter_ns();decode_cycles=thread_cycles();result=ProcessSamples(payload)
   parent_decode_cycles=thread_cycles()-decode_cycles
   parent_decode_ns=time.perf_counter_ns()-received
   self.previous=newer;self.previous_generation=generation
   if len(self.stage_samples)<10000:self.stage_samples.append(dict(parent_received_ns=received,parent_completed_ns=time.perf_counter_ns(),shared_read=shared_read,prepared_sample_count=len(alphas),history_only=result.history_only,older=older[1].graph.refresh,newer=newer[1].graph.refresh,child_prepare_ns=elapsed,child_stages=child_stages,parent_output_decode_ns=parent_decode_ns,parent_output_decode_cycles=parent_decode_cycles,parent_decode_stages=result.decode_stages,input_reused=bool(reuse),input_transferred_bytes=input_bytes,output_original_bytes=payload['original_bytes'],output_transferred_bytes=payload['transferred_bytes'],ipc_and_prepare_ns=time.perf_counter_ns()-started))
   return result
  return self.pipeline.submit(prepare,timeout=timeout,abort=abort,identity=(older[1].graph.epoch,older[1].graph.refresh,newer[1].graph.refresh))
 def take(self,future):return self.pipeline.take(future)
 def invalidate(self):self.pipeline.invalidate()
 def close(self):
  self.pipeline.close()
  forced=False
  try:
   if self.process.is_alive():self.connection.send(None);self.process.join(5)
  finally:
   if self.process.is_alive():forced=True;self.process.terminate();self.process.join(5)
   self.connection.close()
   if self.process.is_alive():raise RuntimeError("Preparation child shutdown failed; shared mapping retained")
   if self.shared_owner is not None:self.shared_owner.close()
   self.previous=None;self.previous_generation=None
   self.shutdown_evidence=dict(child_pid=self.process.pid,child_alive=self.process.is_alive(),child_exitcode=self.process.exitcode,forced_termination=forced,connection_closed=self.connection.closed,shared_mapping_closed=self.shared_owner.closed if self.shared_owner is not None else None,retained_previous_scene=False)
