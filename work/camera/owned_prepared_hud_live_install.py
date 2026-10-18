import ctypes as C
from pathlib import Path
def install():
 import owned_hud_borrowed_rows_install_candidate as selected
 old=selected.original_cdll
 def load(path,*args,**kwargs):
  if Path(path).name=='owned-gpu-hud-borrowed-rows-candidate.dll':path=str(Path(path).with_name('owned-gpu-hud-prepared-native-candidate.dll'))
  return old(path,*args,**kwargs)
 selected.original_cdll=load
 original=selected.PrefetchSession.prepare
 def prepare(self,*args,**kwargs):
  result=original(self,*args,**kwargs)
  assert Path(self.source._name).name=='owned-gpu-hud-prepared-native-candidate.dll'
  self.source.nf_hud_prepared_rows_used.restype=C.c_uint64
  self.source.nf_hud_owner_prepared_bytes.restype=C.c_uint64
  result['native_prepared_hud_rows_used']=self.source.nf_hud_prepared_rows_used()
  result['native_prepared_hud_bytes']=self.source.nf_hud_owner_prepared_bytes()
  return result
 selected.PrefetchSession.prepare=prepare
 original_close=selected.PrefetchSession.close
 def close(self):
  original_close(self)
  self.source.nf_hud_owner_prepared_bytes.restype=C.c_uint64
  remaining=self.source.nf_hud_owner_prepared_bytes()
  assert remaining==0,remaining
  print('NATIVE_PREPARED_HUD_FINAL_BYTES',remaining,flush=True)
 selected.PrefetchSession.close=close
