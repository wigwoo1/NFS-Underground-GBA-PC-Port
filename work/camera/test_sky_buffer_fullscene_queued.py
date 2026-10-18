"""Run existing independent full-scene queued oracle with sky-buffer DLL."""
import runpy,sys,json,ctypes as C
from pathlib import Path
original=Path.read_text
def read(self,*args,**kwargs):
 value=original(self,*args,**kwargs)
 if self.name=='test_segmented_original_gpu_parity.py':
  assert value.count('owned-gpu-segmented-source-candidate.dll')==1
  value=value.replace('owned-gpu-segmented-source-candidate.dll','owned-gpu-segmented-sky-buffer-candidate.dll')
 return value
Path.read_text=read
try:runpy.run_path('work/camera/test_multi_queued_segmented_gpu.py',run_name='__main__')
finally:Path.read_text=original
d=C.CDLL(str(Path('work/camera/owned-gpu-segmented-sky-buffer-candidate.dll').resolve()));s=(C.c_uint64*2)();d.nf_sky_vertex_buffer_stats.argtypes=[C.c_void_p]
assert d.nf_sky_vertex_buffer_stats(s) and s[0]==0 and s[1]>=1
out=Path(sys.argv[2]);r=json.loads(out.read_text());r['sky_vertex_after_close']=list(s);r['sky_buffer_candidate']=True;out.write_text(json.dumps(r,indent=2));print('PASS fullscene queued sky-buffer close',list(s))
