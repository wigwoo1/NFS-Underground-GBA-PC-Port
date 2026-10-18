"""Isolated verified producer sky reuse plus bounded GPU sky vertex storage."""
import runpy
from pathlib import Path
original_read=Path.read_text
TARGET=Path('work/camera/run_segmented_wait_profile_candidate.py').resolve()
def read(self,*args,**kwargs):
 source=original_read(self,*args,**kwargs)
 if self.resolve()==TARGET:
  assert source.count('owned-gpu-segmented-source-candidate.dll')==1
  source=source.replace('owned-gpu-segmented-source-candidate.dll','owned-gpu-segmented-sky-buffer-candidate.dll')
  source=source.replace(" path=Path('work/camera/prototype-runs')"," stats=(C.c_uint64*2)();gpu.nf_sky_vertex_buffer_stats.argtypes=[C.c_void_p]\n assert gpu.nf_sky_vertex_buffer_stats(stats) and stats[0]==0 and stats[1]>=1\n path=Path('work/camera/prototype-runs')")
  source=source.replace('dict(targets=list(targets),fences=list(fences))','dict(targets=list(targets),fences=list(fences),sky_vertex_buffer_stats=list(stats))')
 return source
Path.read_text=read
runpy.run_path('work/camera/run_sky_attached_reuse_candidate.py',run_name='__main__')
