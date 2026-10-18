import ctypes as C,threading,json
from pathlib import Path
from owned_prepared_frame_service_candidate import PreparedFrames,native
raw=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000/older.frame.bin').read_bytes()
import struct
epoch=struct.unpack_from('<Q',raw,24)[0];refresh=struct.unpack_from('<I',raw,4)[0]
Reader=C.CFUNCTYPE(C.c_int,C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t))
entered=threading.Event();release=threading.Event()
@Reader
def reader(e,r,p,n,w):
 w[0]=len(raw)
 if not p:return 1
 entered.set();assert release.wait(10);C.memmove(p,raw,len(raw));return 1
service=PreparedFrames()
with service.cv:assert service.cv.wait_for(lambda:len(service.ready)==2,10)
assert service.peak==2
packets=[];errors=[];shutdown=[]
def consume():
 try:packets.append(service.capture(C.cast(reader,C.c_void_p).value,epoch,refresh))
 except BaseException as e:errors.append(repr(e))
consumer=threading.Thread(target=consume);consumer.start();assert entered.wait(10)
closer=threading.Thread(target=lambda:shutdown.append(service.close()));closer.start()
with service.cv:assert service.cv.wait_for(lambda:service.closed,10)
assert closer.is_alive();assert consumer.is_alive()
release.set();consumer.join(10);closer.join(10)
assert not consumer.is_alive() and not closer.is_alive() and not errors and packets==[raw]
assert shutdown[0]['joined'] and shutdown[0]['pending']==0 and shutdown[0]['peak']==2
assert service.close()['pending']==0
saved=native.prepare
try:
 def fail(size):raise MemoryError('Injected preparation allocation failure')
 native.prepare=fail;failed=PreparedFrames()
 try:
  try:failed.capture(C.cast(reader,C.c_void_p).value,epoch,refresh)
  except RuntimeError as e:assert isinstance(e.__cause__,MemoryError)
  else:raise AssertionError('Preparation failure hidden')
 finally:failure_shutdown=failed.close()
 assert failure_shutdown['joined'] and failure_shutdown['pending']==0
 # Stop while a preparer owns unpublished storage, before queue publication.
 prep_entered=threading.Event();prep_release=threading.Event()
 def held(size):
  capsule=saved(size);prep_entered.set();assert prep_release.wait(10);return capsule
 native.prepare=held;stopped=PreparedFrames();assert prep_entered.wait(10)
 stopped_shutdown=[];stopper=threading.Thread(target=lambda:stopped_shutdown.append(stopped.close()));stopper.start()
 with stopped.cv:assert stopped.cv.wait_for(lambda:stopped.closed,10)
 assert stopper.is_alive();prep_release.set();stopper.join(10);assert not stopper.is_alive()
 assert stopped_shutdown[0]['joined'] and stopped_shutdown[0]['created']==0 and stopped_shutdown[0]['pending']==0
finally:native.prepare=saved
result=dict(result='PASS_PREPARED_STORAGE_FORCED_LIFECYCLE',active_capture_close=shutdown[0],preparation_failure=failure_shutdown,inflight_preparation_close=stopped_shutdown[0],scope='Forced component races using actual private native storage and captured fixture. Not live game integration/all interleavings or60fps proof.')
Path('work/camera/prototype-runs/prepared-storage-races-20261009.json').write_text(json.dumps(result,indent=2));print(result)
