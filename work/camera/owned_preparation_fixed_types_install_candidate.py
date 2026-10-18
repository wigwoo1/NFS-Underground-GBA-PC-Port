"""Reuse only ctypes type definitions; every native buffer remains private."""
import ctypes as C,inspect,textwrap
from functools import lru_cache
import sample_owned_motion as motion
import owned_sampled_road_sequence as road
import owned_source_native_depth_rectangle_candidate as face
Matrix12=C.c_int32*12
World96=C.c_double*96
@lru_cache(maxsize=128)
def char_type(size):
 if type(size) is not int or not 0<=size<=0x100000:raise ValueError('Invalid private character buffer extent')
 return C.c_char*size
def private_string_buffer(init):
 if isinstance(init,bytes):return char_type(len(init)+1).from_buffer_copy(init+b'\0')
 if type(init) is int:return char_type(init)()
 raise TypeError('Expected bytes or integer buffer size')
def install(cls,name,replacements):
 original=getattr(cls,name);source=textwrap.dedent(inspect.getsource(original))
 for old,new in replacements:
  assert old in source;source=source.replace(old,new)
 namespace=dict(original.__globals__,Matrix12=Matrix12,World96=World96,private_string_buffer=private_string_buffer)
 exec(compile(source,'preparation-private-fixed-types','exec'),namespace);setattr(cls,name,namespace[name])
install(motion.PreparedMotionPair,'__init__',[('(C.c_int32*12)','Matrix12')])
install(road.SampledRoadSequence,'sample',[('(C.c_double*96)','World96')])
install(face.SourceFaceDeterminants,'__init__',[('C.create_string_buffer(','private_string_buffer(')])
