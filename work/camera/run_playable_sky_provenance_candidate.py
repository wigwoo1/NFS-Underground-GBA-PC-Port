import runpy
from pathlib import Path
original=Path.read_text
target=Path('work/camera/run_queued_source_anchor_candidate.py').resolve()
def read(path,*args,**kwargs):
 s=original(path,*args,**kwargs)
 if path.resolve()==target:
  assert s.count('owned-sky-source-context-candidate.dll')==1
  s=s.replace('owned-sky-source-context-candidate.dll','owned-gpu-playable-sky-provenance-candidate.dll')
  marker=" path=Path('work/camera/prototype-runs')"
  assert s.count(marker)==1
  export=""" gpu.nf_playable_sky_capture_count.restype=C.c_uint;gpu.nf_playable_sky_capture_read.argtypes=[C.c_uint,C.c_void_p,C.c_void_p,C.c_size_t]
 capture_dir=Path('work/camera/prototype-runs')/('playable-sky-capture-'+str(time.time_ns()));capture_dir.mkdir();capture_records=[]
 for index in range(gpu.nf_playable_sky_capture_count()):
  row=(C.c_uint64*6)();pixels=C.create_string_buffer(3240*16*3);assert gpu.nf_playable_sky_capture_read(index,row,pixels,len(pixels))==0
  pixel_path=capture_dir/(str(index)+'.rgb');pixel_path.write_bytes(pixels.raw);gpu.nf_playable_sky_stage_read.argtypes=[C.c_uint,C.c_void_p,C.c_size_t];assert gpu.nf_playable_sky_stage_read(index,pixels,len(pixels))==0;pixel_path.with_suffix(".sky.rgb").write_bytes(pixels.raw);gpu.nf_playable_prehud_read.argtypes=[C.c_uint,C.c_void_p,C.c_size_t];assert gpu.nf_playable_prehud_read(index,pixels,len(pixels))==0;pixel_path.with_suffix(".prehud.rgb").write_bytes(pixels.raw);hudmask=C.create_string_buffer(480);gpu.nf_playable_hud_mask_read.argtypes=[C.c_uint,C.c_void_p,C.c_size_t];assert gpu.nf_playable_hud_mask_read(index,hudmask,len(hudmask))==0;pixel_path.with_suffix(".hudmask").write_bytes(hudmask.raw);coverage=C.create_string_buffer(3240*16);gpu.nf_playable_world_coverage_read.argtypes=[C.c_uint,C.c_void_p,C.c_size_t];assert gpu.nf_playable_world_coverage_read(index,coverage,len(coverage))==0;pixel_path.with_suffix(".worldmask").write_bytes(coverage.raw);capture_records.append(dict(values=list(row),path=str(pixel_path)))
 assert len(capture_records)==96
"""
  s=s.replace(marker,export+marker).replace('dict(targets=list(targets),fences=list(fences))','dict(targets=list(targets),fences=list(fences),playable_sky_capture=capture_records)')
 return s
Path.read_text=read
runpy.run_path('work/camera/run_source_compact_single_candidate.py',run_name='__main__')


