import ctypes as C,json,hashlib,shutil
from pathlib import Path
from PIL import Image,ImageChops,ImageStat
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/world-palette-candidate-20261007');cp.mkdir(exist_ok=True)
base=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/indexed-scene-capture-20261007');r=json.loads((base/'owned-native-1791388271044014500.json').read_text())
d=C.CDLL(str(Path('work/camera/owned-world-palette-candidate.dll').resolve()));d.nf_palette_candidate_555.argtypes=[C.c_uint16];d.nf_palette_candidate_555.restype=C.c_uint32
for v in range(32768):
 original=((v&31)<<3)|(((v>>5)&31)<<11)|(((v>>10)&31)<<19);original|=(original>>5)&0x070707
 assert d.nf_palette_candidate_555(v)==original
checks=[]
for row in r['wall_diagnostic_frames']:
 images=[];frame=Path(row['original']).read_bytes()
 for name in ['owned-world-gpu.dll','owned-world-palette-candidate.dll']:
  gpu=C.CDLL(str(Path('work/camera',name).resolve()));gpu.nf_owned_gpu_render.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t]
  out=(C.c_ubyte*(3840*2160*3))()
  try:assert gpu.nf_owned_gpu_render(frame,len(frame),out,len(out))==0
  finally:assert gpu.nf_owned_gpu_close()==1
  images.append(Image.frombytes('RGB',(3840,2160),bytes(out)))
 diff=ImageChops.difference(*images);extrema=diff.getextrema();changed=sum(v>0 for v in diff.convert('L').getdata())
 # Count changed pixels directly; luminance conversion can round one-unit diffs to zero.
 changed=sum(any(pixel) for pixel in diff.getdata());assert max(x[1] for x in extrema)<=1
 reference=Path(row['original_video']).read_bytes();scores=[]
 for img in images:
  pix=img.load();error=0;exact=0
  for y in range(160):
   for x in range(240):
    a=pix[int(300+(x+.5)*13.5),int((y+.5)*13.5)];b=reference[(y*240+x)*4:(y*240+x)*4+3];error+=sum(abs(i-j) for i,j in zip(a,b));exact+=tuple(a)==tuple(b)
  scores.append(dict(mae=error/(38400*3),exact_pixels=exact))
 images[1].save(cp/f"candidate-{row['refresh']}.png")
 checks.append(dict(refresh=row['refresh'],changed_4k_pixels=changed,max_channel_difference=max(x[1] for x in extrema),default=scores[0],candidate=scores[1]))
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',palette_colors=32768,checks=checks,scope='Exact original-core bit replication and actual GPU material differences across three captured integer scenes; fixed viewport reference, no fitted matching. Not full visual fidelity.'),indent=2));print(json.dumps(checks))
