from pathlib import Path
import ctypes as C,struct,json,random
class Time(C.Structure):_fields_=[('epoch',C.c_uint64),('older',C.c_uint64),('newer',C.c_uint64),('alpha',C.c_double),('target',C.c_double)]
class Pair(C.Structure):_fields_=[('time',Time),('older',C.c_void_p),('older_size',C.c_size_t),('newer',C.c_void_p),('newer_size',C.c_size_t)]
d=C.CDLL(str(Path('work/camera/snapshot_store.dll').resolve()))
d.nf_snapshot_create.argtypes=[C.c_size_t];d.nf_snapshot_create.restype=C.c_void_p
d.nf_snapshot_push.argtypes=[C.c_void_p,C.c_uint64,C.c_uint64,C.c_double,C.c_void_p,C.c_size_t]
d.nf_snapshot_acquire.argtypes=[C.c_void_p,C.c_double,C.c_double,C.POINTER(Pair)]
d.nf_snapshot_release.argtypes=[C.c_void_p];d.nf_snapshot_destroy.argtypes=[C.c_void_p]
s=d.nf_snapshot_create(8192);assert s;pair=Pair();r=random.Random(160);payloads={}
for i in range(1000):
 data=r.randbytes(r.randrange(16,256));payloads[i]=data;buffer=C.create_string_buffer(data)
 assert d.nf_snapshot_push(s,1,i,i*4,buffer,len(data))
 C.memset(buffer,0,len(data)) # The store must not retain the producer's buffer.
 older=max(0,i-1);target=older*4+(2 if i else 0)
 assert d.nf_snapshot_acquire(s,target,0,C.byref(pair))==2
 assert C.string_at(pair.older,pair.older_size)==payloads[pair.time.older]
 assert C.string_at(pair.newer,pair.newer_size)==payloads[pair.time.newer]
 assert not d.nf_snapshot_push(s,1,i+1,i*4+4,buffer,len(data))
 assert not d.nf_snapshot_destroy(s)
 assert not d.nf_snapshot_acquire(s,target,0,C.byref(Pair()))
 d.nf_snapshot_release(s)
assert not d.nf_snapshot_push(s,1,999,4001,buffer,len(data))
assert not d.nf_snapshot_push(s,0,1001,4001,buffer,len(data))
assert not d.nf_snapshot_push(s,1,1001,4001,buffer,8193)
assert d.nf_snapshot_push(s,2,0,0,buffer,len(data))
assert d.nf_snapshot_acquire(s,0,0,C.byref(pair))==2 and pair.time.epoch==2 and pair.time.older==pair.time.newer==0
d.nf_snapshot_release(s);assert d.nf_snapshot_destroy(s)
s=d.nf_snapshot_create(32);data=C.create_string_buffer(b'x'*24)
assert d.nf_snapshot_push(s,1,1,1,data,24)
assert d.nf_snapshot_push(s,1,2,2,data,24)
assert not d.nf_snapshot_push(s,1,3,3,data,33)
assert d.nf_snapshot_acquire(s,2,0,C.byref(pair))==2 and pair.time.older==2 and C.string_at(pair.older,24)==b'x'*24
d.nf_snapshot_release(s);assert d.nf_snapshot_destroy(s)
s=d.nf_snapshot_create(256);expected=[]
for i in range(1000):
 data=r.randbytes(r.randrange(1,257));buffer=C.create_string_buffer(data)
 assert d.nf_snapshot_push(s,1,i,i,buffer,len(data))
 expected.append((i,data))
 while len(expected)>16 or sum(len(v) for _,v in expected)>256:expected.pop(0)
 for index,(identity,payload) in enumerate(expected):
  assert d.nf_snapshot_acquire(s,identity,0,C.byref(pair))==2
  assert pair.time.older==identity and C.string_at(pair.older,pair.older_size)==payload
  newer=expected[min(index+1,len(expected)-1)]
  assert pair.time.newer==newer[0] and C.string_at(pair.newer,pair.newer_size)==newer[1]
  d.nf_snapshot_release(s)
 assert d.nf_snapshot_acquire(s,expected[0][0]-.5,0,C.byref(pair))!=2
 d.nf_snapshot_release(s)
assert d.nf_snapshot_destroy(s)
report={'result':'PASS','snapshot_copy_and_pin_cycles':1000,'variable_budget_pushes':1000,'checks':['producer mutation isolation','pair lifetime pinning','queue eviction','epoch reset','duplicate/stale rejection','oversize failure preserves existing snapshot','byte-budget eviction matches independent queue'],'scope':'Single-owner opaque payload lifetime and bounded retention; not visible gameplay evidence.'}
Path('work/camera/snapshot-store-tests.json').write_text(json.dumps(report,indent=2));print(report)
