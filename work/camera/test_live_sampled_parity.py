"""Compare final sampled live frame to exported identical offscreen inputs."""
from pathlib import Path
import struct,os,subprocess,json,re
from PIL import Image,ImageChops
p=Path('work/camera').resolve();env=os.environ.copy();env['NF_LIVE_CLIP_EXPORT']=str(p/'sampled-live-pair')
wide=os.getenv('NF_VISIBILITY_WIDE')=='1'
run=subprocess.run([str(p/('live-ordered-preview-wide.exe' if wide else 'live-ordered-preview.exe')),str(p/('visibility-probe-wide.dll' if wide else 'visibility-probe.dll')),'G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba','work/driving.state',str(p/'sampled-live-parity.csv'),str(p/'sampled-live-parity'),'--sampled-clips','--reload'],env=env,check=True,capture_output=True,text=True)
alpha=struct.unpack_from('<d',(p/'sampled-live-pair.clips').read_bytes(),20)[0]
env.update(NF_CAPTURE_CLIPS=str(p/'sampled-live-pair.clips'),NF_PREVIEW_FRACTION=str(alpha),NF_PREVIEW_PHASE='2')
subprocess.run([str(p/'sampled-clip-preview.exe'),str(p/'sampled-live-pair-0.bin'),str(p/'sampled-live-pair-1.bin'),str(p/'sampled-live-offscreen')],env=env,check=True,capture_output=True)
with Image.open(p/'sampled-live-parity-0.ppm') as a,Image.open(p/'sampled-live-offscreen-2.ppm') as b:
 assert a.size==(3840,2160) and ImageChops.difference(a,b).getbbox() is None
entrants=[dict(epoch=int(e),older=int(a),newer=int(b),alpha=float(t),count=int(n)) for e,a,b,t,n in re.findall(r'sampled_entrant epoch=(\d+) older=(\d+) newer=(\d+) alpha=([0-9.]+) count=(\d+)',run.stdout)]
assert len(entrants)==6
assets=[tuple(map(int,row)) for row in re.findall(r'entrant_asset scene=(\d+) source=(\d+) pass=(\d+) flags=(\d+) extracted=(\d+) bytes=(\d+)',run.stdout)]
assert len(assets)==6 and all(row[2:]==(0,4352,1,16556) for row in assets)
assert {(row[0],row[1]) for row in assets}=={(27,139937788),(28,139937312)}
if env.get('NF_LIVE_ENTRANTS'):
 assert 'entrant_live_applied=6 released=6' in run.stdout
 assert 'entrant_fallback=0' in run.stdout
report=dict(result='PASS',changed_pixels=0,alpha=alpha,entrant_frames=entrants,log=run.stdout,scope='Same-input sampled clipping parity at final frame. Final frame only; entrant frame images not compared here. Unpaced, no gameplay timing proof.')
(p/('live-sampled-parity-wide-tests.json' if wide else 'live-sampled-parity-tests.json')).write_text(json.dumps(report,indent=2));print(json.dumps(report))

