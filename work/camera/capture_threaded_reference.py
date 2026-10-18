"""Replay recorded original inputs to both brackets of exported native frame."""
from pathlib import Path
import ctypes as C,csv,json,math,hashlib,sys
from PIL import Image,ImageDraw
p=Path(__file__).resolve().parent
prefix=Path(sys.argv[1]) if len(sys.argv)>1 else p/'prototype-runs/threaded-b624a6c38aaf46d8ac65679c17bdd8c7'
out=p.parents[1]/'outputs/nfsug-native-renderer/camera-research'
rows=list(csv.DictReader(Path(str(prefix)+'-worker.csv').open()));native_row=rows[11];target=float(native_row['target']);wanted={math.floor(target),math.ceil(target)}
provenance=Path(str(prefix)+'-native-source.json')
if provenance.exists():
 metadata=json.loads(provenance.read_text());target=metadata['target'];wanted={math.floor(target),math.ceil(target),*metadata['source_refreshes']}
inputs=list(csv.DictReader(Path(str(prefix)+'-input.csv').open()))
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');state=p.parent/'driving.state'
hashes=[hashlib.sha256(f.read_bytes()).hexdigest() for f in (rom,state)]
d=C.CDLL(str(p.parent/'nfsprobe.dll'));d.nf_init.argtypes=[C.c_char_p]*2;d.nf_state.argtypes=[C.c_char_p,C.c_int];d.nf_pixels.restype=C.c_void_p
assert d.nf_init(str(rom).encode(),b'') and d.nf_state(str(state).encode(),0)
images={}
try:
 for i,row in enumerate(inputs):
  assert int(row['index'])==i and int(row['after'])==int(row['before'])+1
  d.nf_frame(int(row['keys']))
  refresh=int(row['after'])
  if refresh in wanted:
   im=Image.frombytes('RGBA',(240,160),C.string_at(d.nf_pixels(),240*160*4)).convert('RGB');im.save(out/f'threaded-original-{refresh}.png');images[refresh]=im
  if wanted<=images.keys():break
finally:d.nf_close()
assert wanted<=images.keys() and hashes==[hashlib.sha256(f.read_bytes()).hexdigest() for f in (rom,state)]
native=Image.open(Path(str(prefix)+'-native.ppm'));assert native.size==(3840,2160)
canvas=Image.new('RGB',(2560,760),'#080b10');canvas.paste(native.resize((1280,720)),(1280,40))
canvas.paste(images[math.ceil(target)].resize((1080,720),Image.Resampling.NEAREST),(100,40))
text=ImageDraw.Draw(canvas);text.text((100,12),f'Original refresh {math.ceil(target)} (nearest bracket)',fill='white');text.text((1380,12),f'Native interpolated source {target:.9f}',fill='white')
canvas.save(out/'threaded-original-native-comparison.png')
report=dict(result='PASS',native_source_target=target,original_refreshes=sorted(wanted),rom_state_unchanged=True,scope='Original native-resolution framebuffer replay at floor/ceil source brackets and available packet source endpoints. Native sample is interpolated, not an exact same-time original framebuffer. Visual layout comparison only; no polygon matching or pixel-equivalence claim.')
(out/'threaded-original-reference.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
