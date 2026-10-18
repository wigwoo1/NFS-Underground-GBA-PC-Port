from pathlib import Path
import sys
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'work/camera'))
if __name__ == '__main__':
    path=root/'work/camera/run_native_hud_prefetch_generation_candidate.py'
    source=path.read_text()
    marker='from live_native_hud_prefetch_generation_candidate import NativeLiveWorker as Base'
    assert source.count(marker)==1
    source=source.replace(marker,marker+'\nfrom owned_hud_prefetch_nonblocking_wait_install_candidate import install as install_nonblocking_hud_wait\nprint("NONBLOCKING_HUD_HANDOFF",install_nonblocking_hud_wait(Base),flush=True)')
    exec(compile(source,str(path),'exec'),dict(__name__='__main__',__file__=str(path)))
