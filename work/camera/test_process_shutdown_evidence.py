import json,weakref,gc
from pathlib import Path
from multiprocessing.shared_memory import SharedMemory
from owned_process_preparation_service import ProcessPreparationService
if __name__=='__main__':
 class Scene:pass
 checks=[]
 for shared in (False,True):
  service=ProcessPreparationService(b'',2,shared_output=shared);owner=Scene();ref=weakref.ref(owner);service.previous=owner;del owner
  name=service.shared_owner.memory.name if shared else None
  service.close();assert ref() is None
  evidence=service.shutdown_evidence;assert not evidence['child_alive'] and evidence['child_exitcode']==0 and evidence['connection_closed'] and not evidence['retained_previous_scene']
  if shared:
   assert evidence['shared_mapping_closed']
   try:m=SharedMemory(name=name)
   except FileNotFoundError:pass
   else:m.close();raise AssertionError('Shared mapping survived close')
  service.close();checks.append(dict(shared=shared,evidence=evidence,idempotent_close=True))
 cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/process-shutdown-evidence-20261007');cp.mkdir(exist_ok=True);(cp/'tests.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Real spawned idle child and optional mapping shutdown; full active race shutdown requires new live report'),indent=2));print('PASS process lifecycle2 configurations')
