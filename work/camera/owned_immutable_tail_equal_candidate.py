"""Synchronous exact equality of bounded retained immutable byte spans."""
import ctypes as C
from pathlib import Path
from owned_native_frame_join import pointer
library=C.CDLL(str(Path(__file__).with_name('immutable-tail-equal-candidate.dll').resolve()))
library.nf_immutable_tail_equal.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t];library.nf_immutable_tail_equal.restype=C.c_int
def equal(endpoint,offset,tail):
 if type(endpoint)is not bytes or type(tail)is not bytes or type(offset)is not int or not 0<=offset<=len(endpoint) or len(endpoint)-offset!=len(tail) or len(tail)>64*1024*1024:raise ValueError('Invalid immutable comparison bounds')
 result=library.nf_immutable_tail_equal(pointer(endpoint)+offset,pointer(tail),len(tail))
 if result not in (0,1):raise ValueError('Native comparison rejected')
 return result==1
