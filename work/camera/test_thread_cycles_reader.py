import ctypes as C,json,threading
from owned_thread_cycles import read,kernel
original=kernel.QueryThreadCycleTime
original.argtypes=[C.c_void_p,C.POINTER(C.c_uint64)];original.restype=C.c_int
get=kernel.GetCurrentThread;get.restype=C.c_void_p
observed=[]
def check():
 prior=read();total=0
 for i in range(1000):total+=i*i
 value=C.c_uint64();assert original(get(),C.byref(value));after=read()
 assert prior<=value.value<=after
 observed.append(dict(ordered=True,work_cycles=after-prior,total=total))
check();thread=threading.Thread(target=check);thread.start();thread.join(5);assert not thread.is_alive() and len(observed)==2
print(json.dumps(dict(result='PASS',threads=observed,scope='Same Windows current-thread counter via GIL-held reader and original ctypes call; no cadence claim')))
