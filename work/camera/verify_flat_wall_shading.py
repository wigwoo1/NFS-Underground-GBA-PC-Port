"""Compare complete native RGB before/after flat wall shading optimization."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
from PIL import Image
import numpy as np
manifest=Path(sys.argv[1]);session=json.loads(manifest.read_text(encoding='utf-8-sig'));prefix=Path(session['prefix']);p=Path(__file__).resolve().parent
settings={k:v for k,v in os.environ.items() if not k.startswith('NF_')};settings.update(NF_CONTINUOUS_ROAD_UV='1',NF_ROAD_RECIPROCAL=str(p/'road-correction-reciprocal.bin'));checks=[]
for i in range(1,13):
 packet=Path(str(prefix)+f'-capture-{i:02d}-native-scene.bin');images=[]
 for name,exe in [('before','endpoint-scene-before-flat-shade.exe'),('after','endpoint-scene-road-order-preview.exe')]:
  out=p/'prototype-runs'/f'flat-shade-{i:02d}-{name}.ppm';subprocess.run([str(p/exe),str(packet),str(out)],env=settings,check=True,capture_output=True);image=np.asarray(Image.open(str(out)+'-0.ppm'));assert image.shape==(2160,3840,3);images.append(image)
 assert np.array_equal(*images),('flat shade changed RGB',i)
 checks.append(dict(frame=i,packet_sha256=hashlib.sha256(packet.read_bytes()).hexdigest(),rgb_sha256=hashlib.sha256(images[0].tobytes()).hexdigest(),rgb_exact=True))
report=dict(result='PASS',frames=checks,scope='Complete native 3840x2160 RGB identical before/after constant-intensity wall optimization on twelve fractional scenes; original raster fidelity, timing and scanout separate.')
Path(str(prefix)+'-flat-shade-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(result='PASS',full_scene_4K_frames=len(checks))))
