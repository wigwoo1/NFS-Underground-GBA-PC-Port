"""Actual state reload with verified opt-in native wait/commit activation."""
import runpy,json
from pathlib import Path
import live_owned_gpu_worker
from live_wait_commit_candidate import WaitCommitWorker
class ActivatedWorker(WaitCommitWorker):
 def __init__(self,*args,**kwargs):
  kwargs['native_present_callback']=True
  super().__init__(*args,**kwargs)
live_owned_gpu_worker.LiveOwnedGPUWorker=ActivatedWorker
ns=runpy.run_path('work/camera/test_continuous_sky_worker_reload.py',run_name='__main__')
counts=[]
for worker in ns['workers']:
 rows=[x for x in worker.results if x.get('native_committed_sample') and x.get('hidden_window_presented')]
 assert rows and all(x.get('native_commit_stage_ns') and x['native_commit_stage_ns'][0]>0 for x in rows)
 counts.append(len(rows))
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-wait-commit-reload-20261007');cp.mkdir(exist_ok=True)
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',cycles=ns['evidence'],verified_native_wait_commit_counts=counts,scope='Actual hidden-window original state reload with native wait/commit activation and clean worker retirement; not sustained cadence/scanout proof.'),indent=2))
print('Verified native wait/commit activation',counts)
