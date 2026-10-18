"""Isolated bounded thread-private visibility buffers; original selection and fallback."""
import ctypes as C,threading
from pathlib import Path
import owned_wall_visibility_candidate as original
local=threading.local()
def buffers():
 if not hasattr(local,'packed'):
  local.packed=(original.Input*4096)();local.out=(original.Output*4096)()
 return local.packed,local.out
def table(values):
 if not isinstance(values,tuple):raise ValueError('Diagnostic reciprocal must be immutable')
 if getattr(local,'table_owner',None) is not values:
  local.table_buffer=(C.c_uint32*len(values))(*values);local.table_owner=values
 return local.table_buffer
source=Path(original.__file__).read_text()
source=source.replace('input_type,output_type=batch_types(len(calls))\n packed=input_type()','packed,out=buffers()')
source=source.replace('out=output_type();status=','status=')
source=source.replace('for v in out)','for v in out[:len(calls)])')
namespace=dict(buffers=buffers,__file__=original.__file__)
exec(compile(source,'visibility_private_buffers','exec'),namespace)
namespace['table']=table
# Preserve ABI types for shared original helper.
namespace['helper']=original.helper
impl=namespace['batch'];reference=original.batch
calls_completed=0
def batch(calls):
 global calls_completed
 if getattr(local,'busy',False):return reference(calls)
 local.busy=True
 try:
  result=impl(calls);calls_completed+=1;return result
 finally:local.busy=False

def install():original.batch=batch
