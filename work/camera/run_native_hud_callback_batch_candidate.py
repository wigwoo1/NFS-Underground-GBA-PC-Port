"""Opt-in existing smoother-sky launcher with combined HUD callback/stages."""
import os,runpy,json
from pathlib import Path
if __name__=='__main__':
 selected=os.environ.get('NFSUG_HUD_CALLBACK_STAGE_BATCH')=='1'
 batch=None
 if selected:
  import owned_hud_callback_stage_batch_candidate as batch
  batch.install()
 try:runpy.run_path(str(Path(__file__).with_name('run_native_long_sky_linear_candidate.py')),run_name='__main__')
 finally:
  evidence=dict(selected=selected,stats=None if batch is None else dict(batch.stats))
  if batch is not None:
   assert batch.stats['calls']>0,'Live wrappers lost batching selection'
   batch.uninstall()
  Path('work/camera/prototype-runs/hud-callback-stage-batch-selection-'+('on' if selected else 'off')+'-20261010.json').write_text(json.dumps(evidence,indent=2))
  print('HUD_CALLBACK_BATCH_SELECTION',evidence,flush=True)
