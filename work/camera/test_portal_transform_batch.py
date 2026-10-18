import ctypes as C,random,time,statistics,json
from pathlib import Path
from owned_portal_transform import transform
lib=C.CDLL(str(Path('work/camera/portal-transform-batch.dll').resolve()));fn=lib.nf_portal_transform_batch;P=C.POINTER(C.c_int32);fn.argtypes=[P,C.c_size_t,P,P,P]
r=random.Random(61006);cases=[]
for _ in range(313):
 points=[(r.randint(-2147483648,2147483647),r.randint(-2147483648,2147483647)) for _ in range(32)]
 a=tuple(r.randint(-2147483648,2147483647) for _ in range(12));b=tuple(r.randint(-2147483648,2147483647) for _ in range(12));cases.append((points,a,b))
def native(points,a,b):
 packed=(C.c_int32*(len(points)*2))(*(v for p in points for v in p));ma=(C.c_int32*12)(*a);mb=(C.c_int32*12)(*b);out=(C.c_int32*(len(points)*4))();assert fn(packed,len(points),ma,mb,out);return tuple(out)
def prior(points,a,b):return tuple(v for x,z in points for m in (a,b) for v in transform(x,z,m))
for args in cases:assert native(*args)==prior(*args)
times={}
for name,call in [('python',prior),('native',native)]:
 batches=[]
 for _ in range(5):
  start=time.perf_counter_ns()
  for args in cases:call(*args)
  batches.append((time.perf_counter_ns()-start)/1e6)
 times[name]=statistics.median(batches)
result=dict(result='PASS_EXACT_TRANSFORM_BATCH',points=313*32,median_batch_ms=times,scope='Diagnostic native candidate includes ctypes packing; not integrated live renderer')
Path('work/camera/portal-transform-batch-tests.json').write_text(json.dumps(result,indent=2));print(result)
