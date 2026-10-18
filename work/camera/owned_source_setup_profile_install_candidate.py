"""Isolated source setup profiler selection and bounded prepared-frame stamps."""
import ctypes as C
from pathlib import Path
from owned_hud_prefetch_d3d_profile_install_candidate import PrefetchSession
original_cdll=C.CDLL;loads=[]
def load(path,*args,**kwargs):
 if Path(path).name=='owned-gpu-source-profile-provenance-candidate.dll':
  path=str(Path(path).with_name('owned-gpu-source-setup-profile-candidate.dll'));loads.append(path)
 return original_cdll(path,*args,**kwargs)
C.CDLL=load
original_prepare=PrefetchSession.prepare
def prepare(self,*args,**kwargs):
 result=original_prepare(self,*args,**kwargs);values=(C.c_uint64*4)()
 assert self.source.nf_source_setup_ticks(values)==1
 stamps=list(values);assert stamps==sorted(stamps) and stamps[0]>0
 result['source_setup_ticks']=stamps;return result
PrefetchSession.prepare=prepare
print('SOURCE_SETUP_PROFILE_SELECTED',flush=True)
