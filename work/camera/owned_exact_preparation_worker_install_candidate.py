"""Isolated exact frame preparation tied to native worker lifetime."""
import owned_async_handoff_worker_install_candidate
import _owned_frame_capture_profile_candidate as extension
from owned_exact_prepared_service_candidate import ExactPreparedFrames
from live_native_hud_prefetch_generation_candidate import NativeLiveWorker
service=ExactPreparedFrames()
original_close=NativeLiveWorker.close
extension.capture=service.capture
extension.last_profile=lambda:()
def close(self):
 if self.owner is None:return original_close(self)
 shutdown=service.close();shutdown['owner_alive_after_preparation_join']=self.owner is not None
 self.frame_preparation_shutdown=shutdown
 try:return original_close(self)
 finally:shutdown['owner_released_after_renderer_close']=self.owner is None
NativeLiveWorker.close=close

# Diagnostic wrappers preserve existing prepared/fallback capture and sole ownership.
import os
if os.environ.get('NFSUG_EXACT_CAPTURE_TRACE')=='1':
 import time,threading
 import owned_exact_prepared_service_candidate as prepared_service
 if os.environ.get('NFSUG_EXACT_CAPTURE_NATIVE_TIMING')=='1':
  import _owned_frame_capture_exact_timed as exact_timed
  import _owned_frame_capture_release_timed as release_timed
  prepared_service.native=exact_timed;prepared_service.fallback=release_timed
 reader_phase_getter=None
 if os.environ.get('NFSUG_PRIVATE_READER_TIMING')=='1':
  import ctypes as C,sys
  from pathlib import Path
  reader_dll=C.CDLL(str(Path('work/camera/'+sys.argv[sys.argv.index('--capture-probe-candidate')+1]).resolve()))
  reader_phase_getter=reader_dll.nf_native_private_reader_phase
  reader_phase_getter.argtypes=[C.c_void_p,C.c_size_t];reader_phase_getter.restype=C.c_int
 def reader_profile():
  if reader_phase_getter is None:return None
  out=(C.c_uint64*10)();assert reader_phase_getter(out,C.sizeof(out))==1
  return list(out)
 capture_trace=threading.local()
 capture_totals={'captures':0,'prepared':0,'fallback':0,'slow_total':0,'slow_retained':[],'max_call_ns':0,'reader_parity_frames':0,'reader_guard_checks':0}

 def timed_call(name,original):
  def call(*args,**kwargs):
   begin=time.perf_counter_ns()
   try:return original(*args,**kwargs)
   finally:
    end=time.perf_counter_ns()
    if hasattr(capture_trace,'rows'):capture_trace.rows.append(dict(phase=name,begin_ns=begin,end_ns=end,native_stats=getattr(getattr(original,'__self__',None),'stats',lambda:None)()))
  return call
 prepared_service.native.frame_size=timed_call('frame_size',prepared_service.native.frame_size)
 prepared_service.native.capture=timed_call('prepared_capture',prepared_service.native.capture)
 prepared_service.fallback.capture=timed_call('fallback_capture',prepared_service.fallback.capture)
 import inspect,textwrap
 service_source=textwrap.dedent(inspect.getsource(prepared_service.ExactPreparedFrames.capture))
 service_source=service_source.replace(' with self.capture_lock:', " capture_trace.service_rows=[('entry',time.perf_counter_ns())]\n with self.capture_lock:\n  capture_trace.service_rows.append(('service_lock_acquired',time.perf_counter_ns()))")
 service_source=service_source.replace('  with self.cv:', "  capture_trace.service_rows.append(('cv_wait_begin',time.perf_counter_ns()))\n  with self.cv:\n   capture_trace.service_rows.append(('cv_acquired',time.perf_counter_ns()))")
 service_source=service_source.replace('  size=native.frame_size', "  capture_trace.service_rows.append(('size_begin',time.perf_counter_ns()))\n  size=native.frame_size")
 service_source=service_source.replace('  return fallback.capture', "  capture_trace.service_rows.append(('buffer_selected',time.perf_counter_ns()))\n  return fallback.capture")
 service_namespace=dict(prepared_service.__dict__,capture_trace=capture_trace,time=time)
 exec(compile(service_source,'exact-capture-service-boundaries','exec'),service_namespace)
 prepared_service.ExactPreparedFrames.capture=service_namespace['capture']
 original_capture=service.capture
 def traced_capture(*args):
  capture_trace.rows=[];begin=time.perf_counter_ns()
  try:
   packet=original_capture(*args)
   if os.environ.get('NFSUG_PRIVATE_READER_PARITY')=='1' and capture_totals['reader_parity_frames']<min(240,int(os.environ.get('NFSUG_PRIVATE_READER_PARITY_FRAMES','20'))):
    transactional=reader_dll.nf_native_owned_frame_read
    transactional.argtypes=[C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)];transactional.restype=C.c_int
    buffer=C.create_string_buffer(len(packet));written=C.c_size_t()
    assert transactional(args[1],args[2],buffer,len(packet),C.byref(written))==1 and written.value==len(packet) and buffer.raw==packet
    if os.environ.get('NFSUG_PRIVATE_READER_GUARDS')=='1':
     private=reader_dll.nf_native_owned_frame_read_private
     private.argtypes=transactional.argtypes;private.restype=C.c_int
     for test_epoch,test_refresh in ((args[1],args[2]),(args[1]+1,args[2]),(args[1],args[2]+1000),(0,args[2])):
      sentinel=C.create_string_buffer(b'X'*16);bad_written=C.c_size_t(123)
      assert private(test_epoch,test_refresh,sentinel,16,C.byref(bad_written))==0
      assert sentinel.raw==b'X'*16+b'\0' and bad_written.value==123
      capture_totals['reader_guard_checks']+=1
    capture_totals['reader_parity_frames']+=1
   return packet
  finally:
   end=time.perf_counter_ns();capture_trace.profile=dict(begin_ns=begin,end_ns=end,rows=capture_trace.rows,reader_phase=reader_profile(),service_rows=getattr(capture_trace,'service_rows',[]),thread=threading.get_ident(),epoch=args[1],refresh=args[2])
   capture_totals['captures']+=1;capture_totals['max_call_ns']=max(capture_totals['max_call_ns'],end-begin)
   path=capture_trace.rows[-1]['phase'] if capture_trace.rows else 'unknown'
   if path=='prepared_capture':capture_totals['prepared']+=1
   elif path=='fallback_capture':capture_totals['fallback']+=1
   if end-begin>10000000:
    capture_totals['slow_total']+=1
    capture_totals['slow_retained'].append(capture_trace.profile)
    capture_totals['slow_retained'].sort(key=lambda p:p['end_ns']-p['begin_ns'],reverse=True)
    del capture_totals['slow_retained'][32:]

 extension.capture=traced_capture
 extension.last_exact_profile=lambda:getattr(capture_trace,'profile',None)
