import ctypes as C,json,hashlib
from pathlib import Path
from PIL import Image,ImageChops
p=Path('work/camera');cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/cross-renderer-colour-parity-20261007');cp.mkdir(exist_ok=True)
checks=[]
for refresh in (8758,8762,8766,8769,8773,8776,8780):
 frame=(p/f'motion-actual-scanline-assets/{refresh}-native-complete-frame.bin').read_bytes();images=[]
 for dll in ('owned-world-gpu.dll','owned-sky-source-context-candidate.dll'):
  d=C.CDLL(str((p/dll).resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];b=C.create_string_buffer(frame);rgb=C.create_string_buffer(3840*2160*3)
  try:assert d.nf_owned_gpu_draw(b,len(frame))==0;assert d.nf_owned_gpu_read(rgb,len(rgb))==0;images.append(Image.frombytes('RGB',(3840,2160),rgb.raw))
  finally:assert d.nf_owned_gpu_close()
 lut=list(range(256))
 for v in range(32):lut[v*255//31]=(v<<3)|(v>>2)
 corrected=images[0].point(lut*3);diff=ImageChops.difference(corrected,images[1]);maximum=ImageChops.lighter(ImageChops.lighter(*diff.split()[:2]),diff.split()[2]);hist=maximum.histogram()
 raw=ImageChops.difference(images[0],images[1]);check=dict(refresh=refresh,raw_bbox=raw.getbbox(),corrected_changed_pixels=8294400-hist[0],corrected_max_channel=max(i for i,n in enumerate(hist) if n),corrected_bbox=diff.getbbox());checks.append(check)
 if refresh==8758:
  images[0].save(cp/'legacy.png');images[1].save(cp/'source.png');diff.save(cp/'corrected-difference.png')
result=dict(checks=checks,result='PASS_COLOUR_ONLY_DIFFERENCES' if all(x['corrected_changed_pixels']==0 for x in checks) else 'RESIDUAL_DIFFERENCES',scope='Captured endpoint frame replay; legacy output channels mapped floor(v*255/31) to bit replication. Not fractional source-context, scanout or gameplay fidelity proof.')
(cp/'tests.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
