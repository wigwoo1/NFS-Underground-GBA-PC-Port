"""Isolated renderer-owner input scratch/ABI reuse; native call order unchanged."""
import ast,dis,textwrap,ctypes as C
from pathlib import Path
import json,time,atexit,os
records=[]
SCRATCH_FIELDS=('input_scratch_owner','input_scratch_state','input_scratch_elapsed','input_scratch_stages','input_scratch_message')
def release(self):
 if self.thread.is_alive():raise RuntimeError('Cannot release live renderer input scratch')
 for name in SCRATCH_FIELDS:
  if hasattr(self,name):delattr(self,name)
 if hasattr(self,'input_scratch_stats'):self.input_scratch_stats.update(closed=True,released=True)
def save():
 if not records:return
 path=Path('work/camera/prototype-runs')/('input-scratch-execution-'+str(time.time_ns())+'.json')
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(dict(records=records,scope='Scalar input reuse and post-worker-join release evidence; no physical controller or cadence claim.'),indent=2));print('INPUT_SCRATCH_EXECUTION',path)
atexit.register(save)
import owned_native_source_segmented_release_worker_candidate as module

def install():
 cls=module.NativeSourceWorker
 if getattr(cls,'input_scratch_candidate',False):return
 method=cls._poll_input
 file_source=Path(module.__file__).read_text();tree=ast.parse(file_source)
 node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='_poll_input')
 source=textwrap.dedent('\n'.join(file_source.splitlines()[node.lineno-1:node.end_lineno]))
 if 'Input4' in method.__code__.co_names:source=source.replace('(C.c_uint32*4)()','Input4()')
 check=dict(method.__globals__);exec(compile(source,'original-input-method-guard','exec'),check)
 assert [(x.opname,x.argval) for x in dis.get_instructions(check['_poll_input'])]==[(x.opname,x.argval) for x in dis.get_instructions(method)],'Unexpected current input method body: '+repr([(a.opname,a.argval,b.opname,b.argval) for a,b in zip(dis.get_instructions(check['_poll_input']),dis.get_instructions(method)) if (a.opname,a.argval)!=(b.opname,b.argval)][:4])
 marker='state=Input4()' if 'Input4' in method.__code__.co_names else 'state=(C.c_uint32*4)()';assert source.count(marker)==1
 source=source.replace(marker,"""s=session.source
 if not hasattr(self,'input_scratch_owner'):
  self.input_scratch_stats=dict(initializations=1,polls=0,reuses=0,traced=self.input_poll_trace,closed=False,released=False)
  records.append(self.input_scratch_stats)
  self.input_scratch_owner=s
  self.input_scratch_state=(C.c_uint32*4)()
  self.input_scratch_elapsed=C.c_uint64()
  self.input_scratch_stages=(C.c_uint64*4)()
  self.input_scratch_message=(C.c_uint64*6)()
  if self.input_poll_trace:
   s.nf_owned_input_poll_timed.argtypes=[C.c_void_p]
   s.nf_owned_input_stages.argtypes=[C.c_void_p]
   if hasattr(s,'nf_owned_input_message_profile'):s.nf_owned_input_message_profile.argtypes=[C.c_void_p]
 elif self.input_scratch_owner is not s:raise RuntimeError('Input scratch source owner changed')
 state=self.input_scratch_state""")
 source=source.replace('elapsed=C.c_uint64();stages=(C.c_uint64*4)()','elapsed=self.input_scratch_elapsed;stages=self.input_scratch_stages')
 source=source.replace('session.source.nf_owned_input_poll_timed.argtypes=[C.c_void_p]','').replace('session.source.nf_owned_input_stages.argtypes=[C.c_void_p]','')
 source=source.replace('values=(C.c_uint64*6)();session.source.nf_owned_input_message_profile.argtypes=[C.c_void_p]','values=self.input_scratch_message')
 source+="\n self.input_scratch_stats['reuses']+=self.input_scratch_stats['polls']>0\n self.input_scratch_stats['polls']+=1\n"
 ns=dict(method.__globals__,records=records);exec(compile(source,'owner-input-scratch-candidate','exec'),ns);cls._poll_input=ns['_poll_input'];cls.input_scratch_candidate=True
 original_close=cls.close
 def close(self):
  try:return original_close(self)
  finally:
   if not self.thread.is_alive():release(self)
 cls.close=close
selected=os.environ.get('NFSUG_INPUT_SCRATCH_SELECT','1')=='1'
if selected:install()
print('INPUT_SCRATCH_SELECTION',selected)





