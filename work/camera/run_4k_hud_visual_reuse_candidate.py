"""Isolated optimized4K HUD visual reuse with retained hit/miss diagnostics."""
import runpy
from pathlib import Path
original_read=Path.read_text;target=Path('work/camera/run_segmented_wait_profile_candidate.py').resolve()
def read(path,*args,**kwargs):
 source=original_read(path,*args,**kwargs)
 if path.resolve()==target:
  assert source.count('owned-gpu-segmented-source-candidate.dll')==1
  source=source.replace('owned-gpu-segmented-source-candidate.dll','owned-gpu-segmented-4k-hud-reuse-candidate.dll')
  marker=" path=Path('work/camera/prototype-runs')";assert source.count(marker)==1
  source=source.replace(marker," stats=(C.c_uint64*2)();gpu.nf_hud_visual_cache_stats.argtypes=[C.c_void_p];assert gpu.nf_hud_visual_cache_stats(stats)\n"+marker)
  source=source.replace('dict(targets=list(targets),fences=list(fences))','dict(targets=list(targets),fences=list(fences),hud_visual_cache_stats=list(stats))')
 return source
Path.read_text=read
runpy.run_path('work/camera/run_sky_attached_reuse_candidate.py',run_name='__main__')
