"""Diagnostic live immutable-frame bridge; GPU context lives on consumer thread."""
from pathlib import Path
import ctypes as C,threading,queue,struct,hashlib,time
class LiveOwnedGPUWorker:
 def __init__(self,epoch,draw_only=False,present=False,paced=False,verify=True,delay_refreshes=24,expected_frames=7,show_window=False,interpolate=False,diagnostic_finish=False):
  self.diagnostic_finish=diagnostic_finish
  self.interpolate=interpolate
  if interpolate:assert draw_only and present and paced and not verify and expected_frames is None
  self.show_window=show_window;self.input_ready=threading.Event();self.input_gpu=None
  self.paused=False;self.pause_begin=None;self.pause_events=[];self.expected_frames=expected_frames;self.verify=verify;self.paced=paced;self.clock_origin=None;self.clock_base=0;self.delay_refreshes=delay_refreshes;self.draw_only=draw_only;self.present=present;self.p=Path('work/camera').resolve();self.d=C.CDLL(str(self.p/'owned-frame-handoff.dll'));P=C.c_void_p;Z=C.c_size_t
  for name,args,result in [('create',[C.c_uint64],P),('push',[P,P,Z],C.c_int),('pop',[P,P],P),('destroy',[P],None)]:
   f=getattr(self.d,'nf_owned_handoff_'+name);f.argtypes=args;f.restype=result
  self.d.nf_owned_handoff_pop_token.argtypes=[P,P,P];self.d.nf_owned_handoff_pop_token.restype=P;self.d.nf_owned_frame_free.argtypes=[P];self.d.nf_owned_handoff_create_capacity.argtypes=[C.c_uint64,C.c_uint];self.d.nf_owned_handoff_create_capacity.restype=P;self.capacity=min(8,max(3,(delay_refreshes+2)//3+2)) if paced else 3;self.owner=self.d.nf_owned_handoff_create_capacity(epoch,self.capacity);assert self.owner
  self.signals=queue.Queue(maxsize=self.capacity);self.space=threading.Semaphore(self.capacity);self.results=[];self.errors=[];self.first_frame_ready=threading.Event();self.epoch=epoch;self.producer=threading.get_ident();self.thread=threading.Thread(target=self.consume);self.thread.start()
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
 def wait_until(self,deadline):
  while True:
   left=deadline-time.perf_counter_ns()
   if left<=0:return
   time.sleep(min(left/1e9,.01))
 def set_paused(self,paused):
  now=time.perf_counter_ns()
  if paused==self.paused:return
  self.d.nf_owned_handoff_pause.argtypes=[C.c_void_p,C.c_uint];assert self.d.nf_owned_handoff_pause(self.owner,int(paused))
  self.paused=paused
  if paused:self.pause_begin=now
  elif self.pause_begin is not None:
   duration=now-self.pause_begin
   if self.clock_origin is not None:self.clock_origin+=duration
   self.pause_events.append(dict(begin_ns=self.pause_begin,end_ns=now,duration_ns=duration));self.pause_begin=None
 def submit(self,frame,bytes_used=None):
  assert threading.get_ident()==self.producer and not self.errors
  assert self.space.acquire(timeout=30),'Renderer queue stalled'
  if not self.d.nf_owned_handoff_push(self.owner,frame,len(frame) if bytes_used is None else bytes_used):
   self.space.release();raise RuntimeError('Native scene handoff rejected')
  self.signals.put(1,timeout=30)
 def draw_intervals(self,gpu,previous,current,generation,refresh,epoch):
  from sample_owned_motion import PreparedMotionPair
  from owned_motion_clock import scene_samples
  gpu.nf_owned_gpu_draw_poses.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_uint]
  Callback=C.CFUNCTYPE(C.c_int,C.c_void_p)
  commit=Callback(lambda ctx:gpu.nf_owned_gpu_present(epoch)==0)
  self.d.nf_owned_handoff_commit_token.argtypes=[C.c_void_p,C.c_uint64,C.c_uint64,Callback,C.c_void_p]
  pair_begin=time.perf_counter_ns();pair=PreparedMotionPair(previous[0],current);pair_prepare_ns=time.perf_counter_ns()-pair_begin
  for slot in scene_samples(self.clock_origin,self.clock_base,previous[2],refresh,self.delay_refreshes):
   assert gpu.nf_owned_input_poll()
   begin=time.perf_counter_ns();frame,cm,models=pair.sample(slot['alpha'])
   pose_end=time.perf_counter_ns()
   if cm is None:assert gpu.nf_owned_gpu_draw(frame,len(frame))==0
   else:assert gpu.nf_owned_gpu_draw_poses(frame,len(frame),cm,models,len(models)//12)==0
   draw_end=time.perf_counter_ns();finish_ns=None
   if self.diagnostic_finish:
    assert gpu.nf_owned_gpu_finish()==0;finish_ns=time.perf_counter_ns()-draw_end
   end=time.perf_counter_ns();self.wait_until(slot['deadline_ns']);present_begin=time.perf_counter_ns()
   committed=self.d.nf_owned_handoff_commit_token(self.owner,epoch,generation,commit,None);assert committed in (0,1)
   self.results.append(dict(refresh=refresh,source_older=previous[2],epoch=epoch,context_count=gpu.nf_owned_gpu_contexts(),consumer_thread=threading.get_ident(),cpu_call_ns=end-begin,timing_scope='pose_prepare_and_draw_cpu',draw_without_readback=True,hidden_window_presented=bool(committed),presentation_deadline_ns=slot['deadline_ns'],present_begin_ns=present_begin,present_end_ns=time.perf_counter_ns(),display_index=slot['index'],alpha=slot['alpha'],interpolated=True,generation=generation,pair_prepare_ns=pair_prepare_ns,pose_sample_cpu_ns=pose_end-begin,draw_cpu_ns=draw_end-pose_end,gpu_completion_wait_ns=finish_ns,gpu_completed_before_present=finish_ns is not None))
   if not committed:return False
  return True
 def consume(self):
  gpu=None;previous=None
  try:
   gpu=C.CDLL(str(self.p/'owned-world-gpu.dll'));gpu.nf_owned_gpu_render.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t];gpu.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];gpu.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];gpu.nf_owned_gpu_present.argtypes=[C.c_uint64]
   if self.present:
    assert gpu.nf_owned_gpu_window(int(self.show_window))==0
    gpu.nf_owned_input_snapshot.argtypes=[C.c_void_p]
    assert gpu.nf_owned_input_poll()
    self.input_gpu=gpu;self.input_ready.set()
   while True:
    if self.present:assert gpu.nf_owned_input_poll()
    try:signal=self.signals.get(timeout=.01)
    except queue.Empty:continue
    if not signal:break
    size=C.c_size_t();generation=C.c_uint64();owner=self.d.nf_owned_handoff_pop_token(self.owner,C.byref(size),C.byref(generation));self.space.release()
    if not owner:continue
    try:
     raw=C.string_at(owner,40);refresh=struct.unpack_from('<I',raw,4)[0];epoch=struct.unpack_from('<Q',raw,24)[0];assert epoch==self.epoch
     if self.interpolate and previous and previous[1]==generation.value and self.clock_origin is not None:
      current=C.string_at(owner,size.value)
      retained=self.draw_intervals(gpu,previous,current,generation.value,refresh,epoch)
      previous=(current,generation.value,refresh) if retained else None
      continue
     rgb=C.create_string_buffer(3840*2160*3) if self.verify else None;begin=time.perf_counter_ns()
     if self.draw_only:
      assert gpu.nf_owned_gpu_draw(owner,size.value)==0;end=time.perf_counter_ns()
      if self.present:
       deadline=None
       if self.paced and self.clock_origin is not None:
        ticks=(refresh-self.clock_base+self.delay_refreshes)*280896
        deadline=self.clock_origin+(ticks*1000000000+16777215)//16777216
        self.wait_until(deadline)
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
     self.results.append(dict(refresh=refresh,epoch=epoch,sha256=hashlib.sha256(rgb.raw).hexdigest() if self.verify else None,context_count=gpu.nf_owned_gpu_contexts(),cpu_call_ns=end-begin,timing_scope="draw_submission_cpu" if self.draw_only else "draw_and_readback_cpu",draw_without_readback=self.draw_only,hidden_window_presented=bool(committed) if self.present else False,consumer_thread=threading.get_ident(),presentation_deadline_ns=deadline if self.present else None,present_begin_ns=present_begin if self.present else None,present_end_ns=present_end if self.present else None))
     if self.interpolate:previous=(C.string_at(owner,size.value),generation.value,refresh) if committed else None
     self.first_frame_ready.set()
    finally:self.d.nf_owned_frame_free(owner)
  except BaseException as e:self.errors.append(repr(e))
  finally:
   if gpu:gpu.nf_owned_gpu_close()
 def close(self):
  self.signals.put(0,timeout=30);self.thread.join(30);assert not self.thread.is_alive(),'GPU worker did not stop'
  self.d.nf_owned_handoff_destroy(self.owner);assert not self.errors,self.errors
  assert (self.expected_frames is None or len(self.results)==self.expected_frames) and all(r['consumer_thread']!=self.producer and r['context_count']==1 for r in self.results)
