"""Isolated command-dispatch timing; frame/sample policy unchanged."""
from pathlib import Path
import owned_native_source_segmented_release_worker_candidate as module
source=Path(module.__file__).read_text().replace('import queue,threading,ctypes as C,hashlib','import queue,threading,ctypes as C,hashlib,time')
source=source.replace('self._put((kind,owned,epoch,generation,index,diagnostic,future))','self._put((kind,owned,epoch,generation,index,diagnostic,time.perf_counter_ns(),future))')
source=source.replace('kind,owned,e,g,i,diagnostic,future=job','kind,owned,e,g,i,diagnostic,submitted_ns,future=job;started_ns=time.perf_counter_ns()')
source=source.replace('self.completed+=1;future.set_result(result)',"completed_ns=time.perf_counter_ns()\n     if isinstance(result,dict):result['renderer_dispatch']=dict(kind=kind,submitted_ns=submitted_ns,started_ns=started_ns,completed_ns=completed_ns,thread=threading.get_ident())\n     self.completed+=1;future.set_result(result)")
source=source.replace('session=None','session=None;previous_job_completed_ns=None',1)
source=source.replace('    self._poll_input(session)\n    try:job=self.jobs.get(timeout=.01)', '    poll_begin_ns=time.perf_counter_ns();self._poll_input(session);poll_end_ns=time.perf_counter_ns()\n    dequeue_begin_ns=time.perf_counter_ns()\n    try:job=self.jobs.get(timeout=.01)')
source=source.replace('kind,owned,e,g,i,diagnostic,submitted_ns,future=job;started_ns=time.perf_counter_ns()', 'dequeued_ns=time.perf_counter_ns()\n    kind,owned,e,g,i,diagnostic,submitted_ns,future=job;started_ns=time.perf_counter_ns()')
source=source.replace('thread=threading.get_ident())', 'thread=threading.get_ident(),previous_job_completed_ns=previous_job_completed_ns,poll_begin_ns=poll_begin_ns,poll_end_ns=poll_end_ns,dequeue_begin_ns=dequeue_begin_ns,dequeued_ns=dequeued_ns,input_poll_stages=getattr(self,\"last_input_poll_stages\",None),input_message_profile=getattr(self,\"last_input_message_profile\",None))')
source=source.replace('self.completed+=1;future.set_result(result)','previous_job_completed_ns=completed_ns;self.completed+=1;future.set_result(result)')
assert 'dequeued_ns=dequeued_ns' in source and 'poll_begin_ns=time.perf_counter_ns()' in source
selected_session=module.NativeSourceSession
namespace=dict(module.__dict__);exec(compile(source,str(Path(module.__file__)),'exec'),namespace)
namespace['NativeSourceSession']=selected_session
module.NativeSourceWorker=namespace['NativeSourceWorker']
