"""Windows current-thread execution cycles; never convert these to elapsed time."""
import ctypes as C
kernel=C.WinDLL('kernel32',use_last_error=True)
# These bounded read-only calls do not wait on renderer or game locks.
# Keep the GIL: releasing it for each profiling read can distort the stage.
held_kernel=C.PyDLL('kernel32',use_last_error=True)
query=held_kernel.QueryThreadCycleTime
query.argtypes=[C.c_void_p,C.POINTER(C.c_uint64)];query.restype=C.c_int
current=held_kernel.GetCurrentThread;current.argtypes=[];current.restype=C.c_void_p

def read():
 value=C.c_uint64()
 if not query(current(),C.byref(value)):raise C.WinError(C.get_last_error())
 return value.value
