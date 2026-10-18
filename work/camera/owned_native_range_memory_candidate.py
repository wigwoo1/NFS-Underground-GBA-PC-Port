"""Isolated bounded native range collection; original Python overlap merge/read."""
import ctypes as C,inspect,textwrap
from pathlib import Path
import owned_closed_scene_memory as base
class Range(C.Structure):_fields_=[('address',C.c_uint32),('source',C.c_uint32),('offset',C.c_uint32),('length',C.c_uint32)]
library=C.CDLL(str(Path(__file__).with_name('native-scene-range-collect-candidate.dll')))
native=library.nf_scene_ranges
native.argtypes=[C.c_char_p,C.c_size_t]*4+[C.POINTER(Range),C.c_size_t];native.restype=C.c_int

def collect(graph):
 blobs=(graph.context,graph.geometry,graph.offsets,graph.materials)
 if any(type(blob)is not bytes for blob in blobs):raise ValueError('Immutable range input required')
 args=tuple(value for blob in blobs for value in (blob,len(blob)))
 count=native(*args,None,0)
 if not 0<=count<=32768:raise ValueError('Invalid native range inputs')
 output=(Range*count)()
 if native(*args,output,count)!=count:raise ValueError('Native range collection failed')
 return [(row.address,blobs[row.source][row.offset:row.offset+row.length]) for row in output]
source=textwrap.dedent(inspect.getsource(base.ClosedSceneMemory.__init__))
a=source.index(' add(word(84)');b=source.index(' if g.faces:',a)
source=source[:a]+" for address,data in collect(g):add(address,data)\n"+source[b:]
namespace=dict(base.__dict__,collect=collect);exec(compile(source,'native_range_memory','exec'),namespace)
class NativeRangeMemory(base.ClosedSceneMemory):__init__=namespace['__init__']
