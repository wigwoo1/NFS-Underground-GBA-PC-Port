"""Exercise real producer/native handoff with immutable and mutable input ownership."""
import ctypes as C,json,runpy
from pathlib import Path
from live_owned_gpu_worker import LiveOwnedGPUWorker
original=LiveOwnedGPUWorker.submit
checks=[]
def submit(self,frame,bytes_used=None,scene=None,replay=False):
 used=len(frame) if bytes_used is None else bytes_used
 supplied=frame
 mutable=type(frame) is bytes and scene is not None and scene.identity[0]==self.epoch and len(checks)%4==3
 if mutable:supplied=C.create_string_buffer(frame)
 result=original(self,supplied,used,scene,replay)
 if scene is not None:
  with self.scene_snapshot_lock:
   owned=self.scene_snapshots[scene.identity][0]
  if type(supplied) is bytes and used==len(supplied):
   assert owned is supplied, 'Immutable frame was copied'
   kind='immutable_identity'
  elif mutable:
   assert owned==frame and type(owned) is bytes
   supplied[0]=bytes([supplied.raw[0]^1])
   assert owned==frame, 'Retained frame borrowed mutable buffer'
   kind='mutable_isolated'
  else:kind='other'
  if self.preparation_previous is not None:assert self.preparation_previous[0] is owned
  checks.append(dict(epoch=self.epoch,refresh=scene.identity[1],kind=kind,replay=replay))
 return result
LiveOwnedGPUWorker.submit=submit
try:runpy.run_path('work/camera/test_continuous_sky_worker_reload.py')
finally:LiveOwnedGPUWorker.submit=original
assert len(checks)>=16 and any(x['kind']=='mutable_isolated' for x in checks)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/sky-submit-ownership-live-20261007');cp.mkdir(exist_ok=True)
(cp/'identity-tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Two actual worker epochs, exact immutable byte identity and native-buffer mutation isolation after submission; not cadence or scanout certification'),indent=2))
print('PASS ownership identity',len(checks),'submissions')
