"""4K pixel parity for source-rebuilt scenery records at activation."""
import runpy,ctypes as C,struct,json,hashlib
from pathlib import Path
from owned_motion_pairs import records
from owned_sampled_supplemental_frame import encode
v=runpy.run_path('work/camera/test_activation_model_record_blocks.py');base=v['fixture']['frames'][1];rebuilt=v['rebuilt_by_descriptor'];rows=records(base)['records'];h=list(struct.unpack_from('<6I2Q',base));tail=base[40+h[2]:]
d=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t]
rgb=C.create_string_buffer(3840*2160*3);checks=[];coverage=[]
try:
 assert d.nf_owned_gpu_draw(base,len(base))==0 and d.nf_owned_gpu_read(rgb,len(rgb))==0;expected=rgb.raw
 for selected in tuple((descriptor,) for descriptor in rebuilt)+(tuple(rebuilt),):
  output=[];replaced=0
  for row in rows:
   copy=dict(row)
   if row['kind']==3 and bytes(row['blocks'][1]) in selected:
    copy['blocks']=rebuilt[bytes(row['blocks'][1])];replaced+=1
   output.append(encode(copy))
  geometry=b''.join(output);header=h.copy();header[2]=len(geometry);frame=struct.pack('<6I2Q',*header)+geometry+tail
  assert d.nf_owned_gpu_draw(frame,len(frame))==0 and d.nf_owned_gpu_read(rgb,len(rgb))==0
  assert rgb.raw==expected,'Source-rebuilt activation frame pixels differ'
  checks.append(dict(replaced_models=replaced,pixels_exact=True))
 for descriptor in rebuilt:
  output=[encode(row) for row in rows if not (row['kind']==3 and bytes(row['blocks'][1])==descriptor)]
  geometry=b''.join(output);header=h.copy();header[2]=len(geometry);frame=struct.pack('<6I2Q',*header)+geometry+tail
  assert d.nf_owned_gpu_draw(frame,len(frame))==0 and d.nf_owned_gpu_read(rgb,len(rgb))==0
  actual=rgb.raw;changed=sum(actual[i:i+3]!=expected[i:i+3] for i in range(0,len(expected),3))
  coverage.append(dict(descriptor_sha256=hashlib.sha256(descriptor).hexdigest(),visible_pixels_changed_when_omitted=changed))
finally:assert d.nf_owned_gpu_close()
assert len(checks)==6 and checks[-1]['replaced_models']==5
out=dict(result='PASS_SOURCE_REBUILT_MODEL_4K_PIXELS',width=3840,height=2160,refresh=records(base)['refresh'],checks=checks,model_visibility_coverage=coverage,reference_rgb_sha256=hashlib.sha256(expected).hexdigest(),scope='Six fullscene endpoint comparisons; fractional motion/visibility and live timing not established.')
(v['fixture']['folder']/'activation-model-4k-pixels.json').write_text(json.dumps(out,indent=2));print('PASS: six pixel-exact 3840x2160 scenes; five source-rebuilt models together')

print('Visible pixel omission coverage:',[x['visible_pixels_changed_when_omitted'] for x in coverage])
