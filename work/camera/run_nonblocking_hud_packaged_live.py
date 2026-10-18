"""Packaged live runner with isolated nonblocking HUD handoff injection."""
from pathlib import Path
import os
import runpy
if __name__=='__main__':
    selected=os.environ.get('NFSUG_HUD_CALLBACK_STAGE_BATCH')=='1'
    batch=None
    if selected:
        import owned_hud_callback_stage_batch_candidate as batch
        batch.install()
    try:
        path=Path(__file__).resolve().with_name('run_native_long_sky_linear_candidate.py')
        source=path.read_text()
        needle=r' import owned_hud_pair_lookahead_install_candidate\n import owned_hud_live_owner_observation_candidate\n'
        assert source.count(needle)==1
        injection=needle+r' import owned_hud_prefetch_nonblocking_wait_install_candidate\n owned_hud_prefetch_nonblocking_wait_install_candidate.install_retirement()\n'
        source=source.replace(needle,injection)
        exec(compile(source,str(path),'exec'),dict(__name__='__main__',__file__=str(path)))
    finally:
        if batch is not None:batch.uninstall()
