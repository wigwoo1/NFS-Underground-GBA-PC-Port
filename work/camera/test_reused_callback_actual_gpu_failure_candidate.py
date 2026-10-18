import runpy,json,hashlib
from pathlib import Path
import owned_commit_callback_reuse_install_candidate as reuse
from live_game_controls import LiveGameControls
original_run=reuse.ReusedAdapter.run;original_step=LiveGameControls.step
worker=None;count=0;injected=False
before=set(Path('work/camera/prototype-runs').glob('owned-native-*.json'))
def step(self):
 global worker
 worker=self.worker;return original_step(self)
def run(self,*args,**kwargs):
 global count,injected
 count+=1
 if count==40:
  previous=kwargs.get('on_prepared')
  def fail():
   global injected
   if previous:previous()
   injected=True;raise RuntimeError('Injected failure after actual GPU prepare before present')
  kwargs['on_prepared']=fail
 return original_run(self,*args,**kwargs)
reuse.ReusedAdapter.run=run;LiveGameControls.step=step
try:
 try:runpy.run_path('work/camera/run_native_reused_commit_callbacks_counted_candidate.py',run_name='__main__')
 except RuntimeError as e:assert injected and 'Injected failure after actual GPU prepare' in str(e),repr(e)
 else:raise AssertionError('GPU prepared failure hidden')
 assert worker is not None and worker.owner is None and not worker.thread.is_alive()
 assert reuse.stats['active']==0
 files=set(Path('work/camera/prototype-runs').glob('owned-native-*.json'))-before;assert len(files)==1
 raw=files.pop();r=json.loads(raw.read_text());assert r['result']=='FAILED' and 'Injected failure after actual GPU prepare' in str(r['error'])
 s=r['shutdown_evidence'];assert not s['gpu_thread_alive'] and not s['preparation_thread_alive'] and s['native_owner_released'] and s['active_contexts_after_close']==0
 f=r['frame_preparation_shutdown'];assert f['joined'] and f['pending']==0 and f['owner_alive_after_preparation_join'] and f['owner_released_after_renderer_close']
 c=r['background_copy_shutdown'];assert not c['thread_alive'] and c['pending']==0
 assert r['hud_lease_cleanup']['owner_stats']==[0,0,0]
 for name,digest in json.loads(Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-committed-sample-20261006/protected-hashes.json').read_text()).items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest().upper()==digest.upper()
 out=dict(result='PASS_ACTUAL_PREPARED_GPU_FAILURE_CLEANUP',raw=str(raw),activation=dict(reuse.stats),shutdown=s,preparation=f,scope='Exception injected after the 40th actual GPU preparation and before presentation; expected FAILED retained, ownership/hash audits pass. Not device removal, driver failure, gameplay timing or scanout qualification.')
 Path('work/camera/prototype-runs/reused-callback-actual-gpu-failure-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
finally:reuse.ReusedAdapter.run=original_run;LiveGameControls.step=original_step
