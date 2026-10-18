"""Endpoint pixel parity, fractional scissor effect and invalid clip rejection."""
from pathlib import Path
import ctypes as C,json,struct,hashlib
from owned_motion_pairs import records
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());d=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_draw_wall_clips.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];rgb=C.create_string_buffer(3840*2160*3);checks=[];fractional_changes=0
try:
 for item in r['wall_diagnostic_frames']:
  frame=Path(item['regenerated']).read_bytes();rows=records(frame)['records'];bounds=(C.c_double*(4*len(rows)))()
  for i,row in enumerate(rows):
   if row['kind']==2:
    for j,v in enumerate(struct.unpack('<4H',row['blocks'][5])):bounds[i*4+j]=v
  assert d.nf_owned_gpu_draw(frame,len(frame))==0;assert d.nf_owned_gpu_read(rgb,len(rgb))==0;expected=rgb.raw
  assert d.nf_owned_gpu_draw_wall_clips(frame,len(frame),None,None,bounds,len(rows))==0;assert d.nf_owned_gpu_read(rgb,len(rgb))==0;assert rgb.raw==expected
  wall_indices=[i for i,row in enumerate(rows) if row['kind']==2];assert wall_indices
  changed=(C.c_double*len(bounds))(*bounds)
  for i in wall_indices:
   if changed[i*4]+.125<=changed[i*4+1]:changed[i*4]+=.125
  assert d.nf_owned_gpu_draw_wall_clips(frame,len(frame),None,None,changed,len(rows))==0;assert d.nf_owned_gpu_read(rgb,len(rgb))==0;different=rgb.raw!=expected;fractional_changes+=different
  bad=(C.c_double*len(bounds))(*bounds);bad[wall_indices[0]*4]=float('nan');assert d.nf_owned_gpu_draw_wall_clips(frame,len(frame),None,None,bad,len(rows))==37
  bad[wall_indices[0]*4]=-1;assert d.nf_owned_gpu_draw_wall_clips(frame,len(frame),None,None,bad,len(rows))==37
  assert d.nf_owned_gpu_draw_wall_clips(frame,len(frame),None,None,bounds,len(rows)-1)==37
  assert d.nf_owned_gpu_draw(frame,len(frame))==0;assert d.nf_owned_gpu_read(rgb,len(rgb))==0;assert rgb.raw==expected
  checks.append(dict(refresh=item['refresh'],endpoint_pixels_exact=8294400,fractional_clip_changes_pixels=different,rgb_sha256=hashlib.sha256(expected).hexdigest()))
finally:assert d.nf_owned_gpu_close()
assert fractional_changes>0
out=dict(result='PASS_FLOAT_WALL_CLIP_GPU_ABI',checks=checks,fractional_changed_frames=fractional_changes,scope='Integer bounds exact at endpoints, fractional clip effect and invalid-input/reset checks; no sampled wall visibility integration or fullscene60fps proof.')
Path('work/camera/float-wall-clip-gpu-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],len(checks),fractional_changes)
