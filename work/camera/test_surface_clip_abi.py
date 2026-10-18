import json,struct,ctypes as C
from pathlib import Path
from owned_motion_pairs import records
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());d=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()))
d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_draw_surface_clips.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t]
rgb=C.create_string_buffer(3840*2160*3);exact=negative=fractional=0
try:
 for f in r['wall_diagnostic_frames']:
  frame=Path(f['regenerated']).read_bytes();rows=records(frame)['records'];bounds=(C.c_double*(4*len(rows)))()
  for i,row in enumerate(rows):
   if row['kind'] in (1,2):bounds[i*4:i*4+4]=struct.unpack('<4H',row['blocks'][5])
  assert d.nf_owned_gpu_draw(frame,len(frame))==0 and d.nf_owned_gpu_read(rgb,len(rgb))==0;expected=rgb.raw
  assert d.nf_owned_gpu_draw_surface_clips(frame,len(frame),None,None,bounds,len(rows))==0 and d.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==expected;exact+=1
  road=next(i for i,row in enumerate(rows) if row['kind']==1);saved=list(bounds[road*4:road*4+4])
  bounds[road*4]=float('nan');assert d.nf_owned_gpu_draw_surface_clips(frame,len(frame),None,None,bounds,len(rows))==37;negative+=1
  bounds[road*4:road*4+4]=saved
  if saved[0]+.25<saved[1]:
   bounds[road*4]=saved[0]+.25
   assert d.nf_owned_gpu_draw_surface_clips(frame,len(frame),None,None,bounds,len(rows))==0 and d.nf_owned_gpu_read(rgb,len(rgb))==0;fractional+=1
  assert d.nf_owned_gpu_draw(frame,len(frame))==0 and d.nf_owned_gpu_read(rgb,len(rgb))==0 and rgb.raw==expected
finally:assert d.nf_owned_gpu_close()
out=dict(result='PASS_SURFACE_CLIP_ABI',endpoint_frames_pixel_exact=exact,invalid_road_bounds_rejected=negative,fractional_road_clip_draws=fractional,override_reset_frames=exact,scope='GPU clipping component only; sampled road source closure and live integration pending')
Path('work/camera/surface-clip-abi-tests.json').write_text(json.dumps(out,indent=2));print(out)
