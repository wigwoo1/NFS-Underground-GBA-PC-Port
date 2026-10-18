"""Diagnostic coverage ablation; production frames and rendering remain unchanged."""
import ctypes as C,json,struct,hashlib,sys,os
from pathlib import Path
from PIL import Image
cp=Path(sys.argv[1]);r=json.loads((cp/'owned-native-1791388271044014500.json').read_text());d=C.CDLL(str(Path('work/camera/owned-world-gpu.dll').resolve()));d.nf_owned_gpu_draw.argtypes=[C.c_void_p,C.c_size_t];d.nf_owned_gpu_read.argtypes=[C.c_void_p,C.c_size_t];rgb=C.create_string_buffer(3840*2160*3)
def draw(frame):
 assert d.nf_owned_gpu_draw(frame,len(frame))==0 and d.nf_owned_gpu_read(rgb,len(rgb))==0
 data=rgb.raw
 return [tuple(data[(int((y+.5)*13.5)*3840+int(300+(x+.5)*13.5))*3:(int((y+.5)*13.5)*3840+int(300+(x+.5)*13.5))*3+3]) for y in range(160) for x in range(240)]
checks=[];crt=C.CDLL('msvcrt');crt._putenv.argtypes=[C.c_char_p];old=os.environ.get('NF_GPU_BACKGROUND_ONLY')
assert old is None,'Diagnostic requires unmodified default world rendering'
try:
 for row in r['wall_diagnostic_frames']:
  frame=Path(row['original']).read_bytes();before=hashlib.sha256(frame).hexdigest();h=struct.unpack_from('<6I2Q',frame);assert h[4:6]==(76800,76800)
  full=draw(frame);masks={}
  for label,offset in [('background',40+h[2]+h[3]),('text',40+h[2]+h[3]+h[4])]:
   altered=bytearray(frame);altered[offset+38400:offset+76800]=bytes(38400);pixels=draw(bytes(altered));masks[label]=[a!=b for a,b in zip(full,pixels)]
  assert crt._putenv(b'NF_GPU_BACKGROUND_ONLY=1')==0
  try:without_world=draw(frame)
  finally:assert crt._putenv(b'NF_GPU_BACKGROUND_ONLY=')==0
  masks['world']=[a!=b for a,b in zip(full,without_world)]
  original=Path(row['original_video']).read_bytes();groups={}
  for i,a in enumerate(full):
   label=('world_changed' if masks['world'][i] else 'background_changed' if masks['background'][i] else 'text_changed' if masks['text'][i] else 'neither_coverage_changed');delta=tuple(abs(x-y) for x,y in zip(a,original[i*4:i*4+3]));groups.setdefault(label,[]).append(delta)
  stats={k:dict(pixels=len(v),exact=sum(max(x)==0 for x in v),within8=sum(max(x)<=8 for x in v),mean_absolute_channel_difference=sum(sum(x) for x in v)/(3*len(v))) for k,v in groups.items()}
  assert hashlib.sha256(Path(row['original']).read_bytes()).hexdigest()==before
  checks.append(dict(refresh=row['refresh'],groups=stats,world_changed=sum(masks['world']),background_changed=sum(masks['background']),text_changed=sum(masks['text']),both_changed=sum(a and b for a,b in zip(masks['background'],masks['text']))))
finally:assert d.nf_owned_gpu_close()
out=dict(result='MEASURED_LAYER_ABLATION_DIFFERENCES',checks=checks,scope='Offscreen diagnostic only: private copies zero captured coverage separately for background/text. Changed final sampled pixels show visible influence, not complete layer membership. World suppression uses existing native diagnostic branch, keeps original HUD/background. Unchanged group can include same-colored world pixels and hardware HUD; world takes reporting precedence, not complete semantic segmentation. No semantic segmentation, fitted alignment, timing or full fidelity certification.')
(cp/'layer-differences.json').write_text(json.dumps(out,indent=2));print(out)
