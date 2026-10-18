"""Reuse six fixed ABI array types; every call still owns fresh buffers."""
import ctypes as C,inspect,textwrap
from owned_uncovered_window_candidate import OwnedD3DConsumer
U64_9=C.c_uint64*9
U64_7=C.c_uint64*7
U32_3=C.c_uint*3
U32_2=C.c_uint*2
F32_4=C.c_float*4

def replace_method(method,replacements):
 source=textwrap.dedent(inspect.getsource(method))
 for old,new in replacements:
  assert old in source,(method.__qualname__,old)
  source=source.replace(old,new)
 namespace=dict(method.__globals__);namespace.update(U64_9=U64_9,U64_7=U64_7,U32_3=U32_3,U32_2=U32_2,F32_4=F32_4)
 exec(compile(source,'fixed-renderer-types','exec'),namespace)
 return namespace[method.__name__]
OwnedD3DConsumer.render=replace_method(OwnedD3DConsumer.render,[('(C.c_uint*3)()', 'U32_3()'),('(C.c_uint*2)()', 'U32_2()'),('(C.c_float*4)(.035,.05,.08,1)','F32_4(.035,.05,.08,1)')])
OwnedD3DConsumer.present=replace_method(OwnedD3DConsumer.present,[('(C.c_uint64*7)()', 'U64_7()'),('(C.c_uint64*9)()', 'U64_9()')])
