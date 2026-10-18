import ctypes as C,time,threading
import owned_native_source_segmented_release_worker_candidate as worker
namespace=worker.NativeSourceWorker._run.__globals__
Base=namespace['NativeSourceSession'];rows=[];dropped=0
class ProfiledSession(Base):
 def prepare(self,owned,epoch,generation,index):
  global dropped
  begin=time.perf_counter_ns();cpu_begin=time.thread_time_ns();result=super().prepare(owned,epoch,generation,index);cpu_end=time.thread_time_ns();end=time.perf_counter_ns()
  native=(C.c_uint64*4)();self.source.nf_owned_gpu_callback_profile.argtypes=[C.c_void_p];assert self.source.nf_owned_gpu_callback_profile(native)==0
  draw=owned.context.draw
  assert draw.started_ns<=draw.completed_ns and native[0]==draw.started_ns and native[3]==draw.completed_ns
  row=dict(epoch=epoch,generation=generation,index=index,thread=threading.get_ident(),begin_ns=begin,end_ns=end,thread_cpu_ns=cpu_end-cpu_begin,native_begin_ns=draw.started_ns,native_end_ns=draw.completed_ns,native_cycles=draw.thread_cycles,native_stages=list(native),hud_build_split=result.get('hud_build_split'),hud_lease_stages=result.get('hud_lease_stages'))
  if len(rows)<4096:rows.append(row)
  else:dropped+=1
  return result
namespace['NativeSourceSession']=ProfiledSession
