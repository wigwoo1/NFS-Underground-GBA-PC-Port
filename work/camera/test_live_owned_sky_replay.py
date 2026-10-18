import ctypes as C,struct,json,math
from pathlib import Path
from owned_sky_sampler import SkySamples
from owned_sky_color import sky_rgba
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/live-owned-sky-replay-20261007')
crt=C.CDLL('msvcrt');assert crt._putenv(b'NF_GPU_BACKGROUND_ONLY=1')==0
p=Path('work/camera');d=C.CDLL(str((p/'owned-sky-queued-targets.dll').resolve()))
api=d.nf_owned_gpu_render_sky;api.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_size_t,C.c_double,C.c_void_p,C.c_size_t]
rgb=C.create_string_buffer(3840*2160*3);checks=[];previous=None
r=json.loads((p/'prototype-runs/owned-native-1791402952123284000.json').read_text());commits={x['sample_begin_ns']:x for x in r['presentation_samples'] if x.get('native_committed_sample')}
try:
 for n in range(80,86):
  prefix=cp/str(n);meta=json.loads(prefix.with_suffix('.json').read_text());row=commits[meta['draw_started_ns']];assert meta['weight']==row['sky_fraction']
  raw=bytearray(prefix.with_suffix('.frame.bin').read_bytes());assert struct.unpack_from('<I',raw)[0]==0x3346474e
  gn,hn=struct.unpack_from('<2I',raw,8);bg=40+gn+hn
  # Remove HUD register effects and require coverage only for this diagnostic replay.
  for y in range(160):
   at=40+gn+y*34944;struct.pack_into('<H',raw,at+8,0x404);struct.pack_into('<3H',raw,at+8+0x50,0,0,0)
  raw[bg+38400+10560:bg+38400+25696]=bytes([1])*15136
  palettes=b''.join(raw[40+gn+y*34944+128+32768:40+gn+y*34944+128+32768+512] for y in range(160))
  lo=prefix.with_suffix('.lower.bin').read_bytes();hi=prefix.with_suffix('.upper.bin').read_bytes();sample=SkySamples(lo,hi,meta['weight'],0x06002940)
  f=C.create_string_buffer(bytes(raw));a=C.create_string_buffer(lo);b=C.create_string_buffer(hi)
  assert api(f,len(raw),a,b,15136,sample.weight,rgb,len(rgb))==0
  pixels=rgb.raw;ref=sky_rgba(sample,palettes);actual=bytearray();maximum=0
  for i in range(15136):
   y,x=divmod(10560+i,240);at=(int((y+.5)*13.5)*3840+int(300+(x+.5)*13.5))*3;color=pixels[at:at+3];actual.extend(color)
   error=max(abs(v-w) for v,w in zip(color,ref[i*4:i*4+3]));maximum=max(maximum,error)
   assert error<=1,(n,i,error)
  changed=None if previous is None else sum(actual[i:i+3]!=previous[i:i+3] for i in range(0,len(actual),3))
  if previous is not None:assert changed>0
  checks.append(dict(draw=n,display_index=row['display_index'],weight=sample.weight,max_channel_error=maximum,changed_centers=changed));previous=actual
finally:assert d.nf_owned_gpu_close()
(cp/'replay.json').write_text(json.dumps(dict(result='PASS_LIVE_INPUT_SKY_ONLY_REPLAY',checks=checks,total_sky_center_checks=6*15136,scope='Original live frame palette/source/fraction captured at six committed draws; replay excludes geometry/HUD effects and forces sky coverage. Actual queued renderer DLL offscreen RGB within one level. Not live fullscene or physical scanout fidelity proof.'),indent=2))
print(json.dumps(checks));print('PASS',6*15136,'sky centers')
