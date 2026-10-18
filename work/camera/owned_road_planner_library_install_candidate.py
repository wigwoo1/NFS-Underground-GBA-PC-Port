"""One road-planner native library wrapper per thread; scratch remains private."""
import ctypes as C,threading,inspect,textwrap
from pathlib import Path
import owned_endpoint_road_planner as module
_local=threading.local()
def road_planner_library():
 library=getattr(_local,'library',None)
 if library is None:
  library=C.CDLL(str(Path('work/camera/visibility-probe-wide.dll').resolve()))
  _local.library=library
 return library
original=module.EndpointRoadPlanner.__init__
source=textwrap.dedent(inspect.getsource(original))
needle="d=C.CDLL(str(Path('work/camera/visibility-probe-wide.dll').resolve()))"
assert source.count(needle)==1
source=source.replace(needle,'d=road_planner_library()')
namespace=dict(original.__globals__,road_planner_library=road_planner_library)
exec(compile(source,'road-planner-thread-library','exec'),namespace)
module.EndpointRoadPlanner.__init__=namespace['__init__']
