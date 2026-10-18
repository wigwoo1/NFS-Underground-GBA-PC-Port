"""Verify isolated 4K window dimensions and existing fractional sky pixels."""
import ctypes as C,json,runpy,sys,os
from pathlib import Path
p=Path('work/camera');cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/source-context-4k-window-20261008');cp.mkdir(exist_ok=True)
d=C.CDLL(str((p/'owned-sky-source-context-4k-candidate.dll').resolve()))
assert d.nf_owned_gpu_window(0)==0
try:
 sys.argv=['check_owned_game_window.py',str(os.getpid()),str(cp/'window.json')]
 runpy.run_path(str(p/'check_owned_game_window.py'),run_name='__main__')
 w=json.loads((cp/'window.json').read_text());assert any(x['client_pixels']==[3840,2160] and x['title']=='NFSUG native renderer diagnostic' for x in w['windows'])
finally:assert d.nf_owned_gpu_close()
s=(p/'test_launcher_sky_fractional_pixels.py').read_text().replace('owned-sky-source-context-candidate.dll','owned-sky-source-context-4k-candidate.dll').replace('launcher-sky-pixels-20261008','source-context-4k-pixels-20261008')
exec(compile(s,'4k_candidate_sky_pixels','exec'))
