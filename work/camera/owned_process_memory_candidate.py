import ctypes as C
class Counters(C.Structure):
 _fields_=[('cb',C.c_ulong),('PageFaultCount',C.c_ulong)]+[(x,C.c_size_t) for x in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage','PrivateUsage')]
k=C.WinDLL('kernel32');k.GetCurrentProcess.restype=C.c_void_p
p=C.WinDLL('psapi');p.GetProcessMemoryInfo.argtypes=[C.c_void_p,C.c_void_p,C.c_ulong]
def read():
 c=Counters();c.cb=C.sizeof(c)
 if not p.GetProcessMemoryInfo(k.GetCurrentProcess(),C.byref(c),c.cb):raise C.WinError()
 return dict(private_bytes=c.PrivateUsage,working_set_bytes=c.WorkingSetSize)
