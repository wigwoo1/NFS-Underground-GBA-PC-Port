"""Thread-local pose DLL wrapper; each scene still owns independent poses/basis."""
import ctypes as C,threading,inspect,textwrap
import owned_scenery_motion as module
_local=threading.local()
def scenery_library():
 if not hasattr(_local,'library'):
  d=C.CDLL(module._rigid_library_path)
  d.nf_model_world_pose.argtypes=[C.c_void_p]*4
  d.nf_rigid_scene_sample.argtypes=[C.c_void_p]*4+[C.c_double,C.c_void_p,C.c_uint,C.c_void_p]
  _local.library=d
 return _local.library
original=module.PreparedSceneryMotion.__init__
source=textwrap.dedent(inspect.getsource(original))
old=' self._lib=C.CDLL(_rigid_library_path)\n self._lib.nf_model_world_pose.argtypes=[C.c_void_p]*4\n self._lib.nf_rigid_scene_sample.argtypes=[C.c_void_p]*4+[C.c_double,C.c_void_p,C.c_uint,C.c_void_p]'
assert source.count(old)==1;source=source.replace(old,' self._lib=scenery_library()')
namespace=dict(original.__globals__,scenery_library=scenery_library);exec(compile(source,'scenery-thread-library','exec'),namespace)
module.PreparedSceneryMotion.__init__=namespace['__init__']
