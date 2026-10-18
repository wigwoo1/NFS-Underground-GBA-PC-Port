"""Read-only current-process metrics; page faults include soft faults."""
import ctypes as C
class Counters(C.Structure):
 _fields_=[("cb",C.c_uint32),("PageFaultCount",C.c_uint32),("PeakWorkingSetSize",C.c_size_t),("WorkingSetSize",C.c_size_t),("QuotaPeakPagedPoolUsage",C.c_size_t),("QuotaPagedPoolUsage",C.c_size_t),("QuotaPeakNonPagedPoolUsage",C.c_size_t),("QuotaNonPagedPoolUsage",C.c_size_t),("PagefileUsage",C.c_size_t),("PeakPagefileUsage",C.c_size_t)]
kernel=C.PyDLL("kernel32",use_last_error=True)
query=kernel.K32GetProcessMemoryInfo;query.argtypes=[C.c_void_p,C.POINTER(Counters),C.c_uint32];query.restype=C.c_int
priority=kernel.GetPriorityClass;priority.argtypes=[C.c_void_p];priority.restype=C.c_uint32
def read():
 value=Counters();value.cb=C.sizeof(value)
 if not query(C.c_void_p(-1),C.byref(value),value.cb):raise C.WinError(C.get_last_error())
 level=priority(C.c_void_p(-1))
 if not level:raise C.WinError(C.get_last_error())
 return dict(page_faults=value.PageFaultCount,working_set_bytes=value.WorkingSetSize,private_commit_bytes=value.PagefileUsage,priority_class=level)
