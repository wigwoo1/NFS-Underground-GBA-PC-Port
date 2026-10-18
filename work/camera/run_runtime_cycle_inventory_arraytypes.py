"""Diagnostic gameplay-only collectible cycle inventory; no pacing claim."""
import gc,runpy,json,collections,ctypes as C
from pathlib import Path
from live_owned_gpu_worker import LiveOwnedGPUWorker
submit=LiveOwnedGPUWorker.submit;close=LiveOwnedGPUWorker.close;before=gc.get_debug();active=False;saved=False

def begin_submit(self,frame,*args,**kwargs):
 global active
 scene=kwargs.get('scene')
 if scene is None and len(args)>1:scene=args[1]
 # Frame header names the actual original refresh, regardless of scene argument form.
 import struct
 header=frame[:40] if isinstance(frame,bytes) else C.string_at(frame,40)
 refresh=struct.unpack_from('<I',header,4)[0]
 if not active and refresh>=8755:
  gc.collect();gc.set_debug(before|gc.DEBUG_SAVEALL);active=True
 return submit(self,frame,*args,**kwargs)

def end_close(self):
 global saved
 if active and not saved:
  gc.collect();saved=True
  counts=collections.Counter(type(x).__module__+'.'+type(x).__qualname__ for x in gc.garbage)
  libraries=collections.Counter(str(x._name) for x in gc.garbage if isinstance(x,C.CDLL))
  arrays=collections.Counter(getattr(x,'_length_',None) for x in gc.garbage if isinstance(x,type) and issubclass(x,C.Array))
  cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/runtime-cycle-inventory-arraytypes-20261007');cp.mkdir(exist_ok=True)
  out=dict(objects=len(gc.garbage),types=counts.most_common(25),library_owners=libraries.most_common(),array_lengths=arrays.most_common(),scope='Collection at first refresh8755 establishes boundary; retained collectible objects inventoried before worker shutdown. DEBUG_SAVEALL and explicit collection invalidate pacing comparison.')
  (cp/'inventory.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
 return close(self)
LiveOwnedGPUWorker.submit=begin_submit;LiveOwnedGPUWorker.close=end_close
try:
 runpy.run_path('work/camera/run_process_transport_dedup_candidate.py',run_name='__main__');assert active and saved
finally:
 LiveOwnedGPUWorker.submit=submit;LiveOwnedGPUWorker.close=close;gc.set_debug(before);gc.garbage.clear()
