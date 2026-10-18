"""One configured visibility wrapper per thread; builders retain private payloads."""
import ctypes as C,threading,inspect,textwrap
from pathlib import Path
import owned_model_record_builder as module
_local=threading.local()
def visibility_library():
 if not hasattr(_local,'library'):
  d=C.CDLL(str(Path('work/camera/visibility-probe-wide.dll').resolve()))
  d.nfs_visibility_object_branch_prepare.argtypes=[C.c_void_p]*7
  d.nfs_visibility_object_material_plan.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,module.Read,C.c_void_p,C.c_void_p,C.c_void_p]
  d.nfs_visibility_object_model_plan.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,module.Read,C.c_void_p,C.c_void_p]
  d.nfs_visibility_object_material.argtypes=[C.c_void_p,C.c_uint,C.c_uint,C.c_void_p]
  d.nfs_visibility_object_texture.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p]
  _local.library=d
 return _local.library
original=module.ModelRecordBuilder.__init__
source=textwrap.dedent(inspect.getsource(original))
start=source.index(' self.lib=C.CDLL(')
source=source[:start]+' self.lib=visibility_library()\n'
namespace=dict(original.__globals__,visibility_library=visibility_library)
exec(compile(source,'visibility-thread-library','exec'),namespace)
module.ModelRecordBuilder.__init__=namespace['__init__']
