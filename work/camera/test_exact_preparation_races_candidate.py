import ctypes as C,struct,threading,json
from pathlib import Path
from owned_exact_prepared_service_candidate import ExactPreparedFrames,native
raw=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000/older.frame.bin').read_bytes();epoch=struct.unpack_from('<Q',raw,24)[0];refresh=struct.unpack_from('<I',raw,4)[0]
variant=bytearray(raw[:40]+b'x'+raw[40:]);struct.pack_into('<I',variant,8,struct.unpack_from('<I',raw,8)[0]+1);variant=bytes(variant);current=raw;queries=0
Reader=C.CFUNCTYPE(C.c_int,C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t))
read_entered=threading.Event();read_release=threading.Event();read_release.set()
@Reader
def reader(e,r,p,n,w):
 global queries
 if not p:queries+=1;w[0]=len(current);return 1
 read_entered.set();assert read_release.wait(10)
 if n<len(current):return 0
 C.memmove(p,current,len(current));w[0]=len(current);return 1
address=C.cast(reader,C.c_void_p).value;saved=native.prepare;prep_entered=threading.Event();prep_release=threading.Event();calls=0
try:
 def held(size):
  global calls
  capsule=saved(size);calls+=1
  if calls==1:prep_entered.set();assert prep_release.wait(10)
  return capsule
 native.prepare=held;service=ExactPreparedFrames()
 assert service.capture(address,epoch,refresh)==raw;assert prep_entered.wait(10)
 current=variant;assert service.capture(address,epoch,refresh)==variant
 prep_release.set()
 with service.cv:assert service.cv.wait_for(lambda:len(service.ready)==2 or service.error,10)
 assert service.discarded>=1 and all(size==len(variant) for size,capsule in service.ready)
 read_entered.clear();read_release.clear();packets=[];errors=[]
 def consume():
  try:packets.append(service.capture(address,epoch,refresh))
  except BaseException as e:errors.append(repr(e))
 consumer=threading.Thread(target=consume);consumer.start();assert read_entered.wait(10)
 shutdown=[];closer=threading.Thread(target=lambda:shutdown.append(service.close()));closer.start()
 with service.cv:assert service.cv.wait_for(lambda:service.closed,10)
 assert closer.is_alive();read_release.set();consumer.join(10);closer.join(10)
 assert not consumer.is_alive() and not closer.is_alive() and not errors and packets==[variant]
 assert shutdown[0]['joined'] and shutdown[0]['pending']==0
 count=queries
 try:service.capture(address,epoch,refresh)
 except RuntimeError:pass
 else:raise AssertionError('Closed capture accepted')
 assert queries==count,'Closed service touched reader'
 def fail(size):raise MemoryError('Injected exact preparation failure')
 native.prepare=fail;failed=ExactPreparedFrames();assert failed.capture(address,epoch,refresh)==variant
 with failed.cv:assert failed.cv.wait_for(lambda:failed.error is not None,10)
 count=queries
 try:failed.capture(address,epoch,refresh)
 except RuntimeError as e:assert isinstance(e.__cause__,MemoryError)
 else:raise AssertionError('Failure hidden')
 assert queries==count
 failure_shutdown=failed.close();assert failure_shutdown['joined'] and failure_shutdown['pending']==0
finally:native.prepare=saved;read_release.set();prep_release.set()
result=dict(result='PASS_EXACT_PREPARATION_FORCED_RACES',stale_and_active_close=shutdown[0],failure_close=failure_shutdown,scope='Native private storage and fixture component races; stale size discard, active capture close, allocation error, no reader calls after close/error. Not actual renderer lifecycle/all races.')
Path('work/camera/prototype-runs/exact-preparation-races-20261009.json').write_text(json.dumps(result,indent=2));print(result)
