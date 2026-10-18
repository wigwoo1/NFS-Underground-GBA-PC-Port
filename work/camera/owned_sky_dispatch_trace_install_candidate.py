"""Isolated command-dispatch timing; frame/sample policy unchanged."""
from pathlib import Path
import owned_native_source_sky_pan_worker_candidate as module
source=Path(module.__file__).read_text().replace('import queue,threading,ctypes as C,hashlib','import queue,threading,ctypes as C,hashlib,time')
source=source.replace('self._put((kind,owned,epoch,generation,index,diagnostic,future))','self._put((kind,owned,epoch,generation,index,diagnostic,time.perf_counter_ns(),future))')
source=source.replace('kind,owned,e,g,i,diagnostic,future=job','kind,owned,e,g,i,diagnostic,submitted_ns,future=job;started_ns=time.perf_counter_ns()')
source=source.replace('self.completed+=1;future.set_result(result)',"completed_ns=time.perf_counter_ns()\n     if isinstance(result,dict):result['renderer_dispatch']=dict(kind=kind,submitted_ns=submitted_ns,started_ns=started_ns,completed_ns=completed_ns,thread=threading.get_ident())\n     self.completed+=1;future.set_result(result)")
selected_session=module.NativeSourceSession
namespace=dict(module.__dict__);exec(compile(source,str(Path(module.__file__)),'exec'),namespace)
namespace['NativeSourceSession']=selected_session
module.NativeSourceWorker=namespace['NativeSourceWorker']
