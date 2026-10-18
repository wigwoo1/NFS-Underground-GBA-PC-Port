from pathlib import Path
import runpy
if __name__=='__main__':
 root=Path(__file__).resolve().parents[2]
 target=(root/'work/camera/run_prepared_hud_packaged.py').resolve()
 alternate=root/'work/camera/run_prepared_hud_packaged_nonblocking.py'
 original_read=Path.read_text
 def read_text(self,*args,**kwargs):
  if self.resolve()==target:return original_read(alternate,*args,**kwargs)
  return original_read(self,*args,**kwargs)
 Path.read_text=read_text
 script=root/'work/camera/run_compact_gap_live.py'
 try:exec(compile(original_read(script),str(script),'exec'),dict(__name__='__main__',__file__=str(script)))
 finally:Path.read_text=original_read
