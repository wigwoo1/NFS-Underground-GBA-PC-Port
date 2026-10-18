"""Reject stale/reloaded input before any worker queue or preparation mutation."""
import ctypes as C,struct,threading
from types import SimpleNamespace
from live_owned_gpu_worker import LiveOwnedGPUWorker
w=LiveOwnedGPUWorker.__new__(LiveOwnedGPUWorker)
w.producer=threading.get_ident();w.epoch=7
# Deliberately no semaphore, retention or preparation fields: rejection must
# precede accessing these resources, including for retained pause replay.
def frame(epoch,refresh=20):return struct.pack('<6I2Q',1,refresh,0,0,0,0,epoch,0)
checks=0
for replay in (False,True):
 for data,size,scene in ((frame(6),None,None),(frame(8),None,SimpleNamespace(identity=(8,20))),(frame(7),None,SimpleNamespace(identity=(6,20))),(frame(7),None,SimpleNamespace(identity=(7,21))),(frame(7),39,None),(frame(7),41,None)):
  for supplied in (data,C.create_string_buffer(data,len(data))):
   try:w.submit(supplied,bytes_used=size,scene=scene,replay=replay)
   except ValueError:checks+=1
   else:raise AssertionError('Invalid input was admitted')
# Valid identity reaches queue admission rather than being rejected.
for data in (frame(7),C.create_string_buffer(frame(7),40)):
 try:w.submit(data,scene=SimpleNamespace(identity=(7,20)))
 except AttributeError as error:assert "errors" in str(error)
 else:raise AssertionError('Expected deliberately absent queue state')
print('PASS',checks,'negative submissions before queue/preparation mutation; valid identity reaches admission')
