"""Three actual corrected transition scenes: palette, repeat and movement."""
import json,os,struct,subprocess,uuid,hashlib,sys
from pathlib import Path
import numpy as np
from PIL import Image
p=Path(__file__).resolve().parent
prefix=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else p/'prototype-runs/threaded-prepared-59aee71d90ee4c88a494da1a6b97ea61'
provenance=json.loads(Path(str(prefix)+'-sampled-provenance.json').read_text());assert provenance['result']=='PASS'
compaction=json.loads(Path(str(prefix)+'-image-compaction.json').read_text());assert compaction['result']=='PASS'
out=p/'prototype-runs'/('indexed-transition-gpu-'+uuid.uuid4().hex);out.mkdir()
checks=[];motion=[];previous=None;previous_cameras=None
for ordinal,proof in enumerate(provenance['checks'],1):
 base=Path(str(prefix)+f'-dense-{ordinal:02d}');packet=Path(str(base)+'-native-scene.bin');raw=packet.read_bytes()
 assert proof['sampled'] and proof['packet_sha256']==hashlib.sha256(raw).hexdigest()
 png=Path(str(base)+'-native.png');record=next(r for r in compaction['records'] if r['lossless_png']==str(png))
 assert record['png_sha256']==hashlib.sha256(png.read_bytes()).hexdigest()
 with Image.open(png) as im:assert im.size==(3840,2160) and hashlib.sha256(im.tobytes()).hexdigest()==record['rgb_sha256']
 camera=Path(str(base)+'-owned-cameras.bin').read_bytes();assert struct.unpack_from('<3I',camera)==(0x5043464e,1,0)
 camera_file=out/'cameras.bin';camera_file.write_bytes(camera[24:])
 hud=Path(str(base)+'-owned-hud.bin').read_bytes();assert len(hud)==160*34944
 palette=b''.join(hud[y*34944+32896:y*34944+33408] for y in range(160));palette_file=out/'palette.bin';palette_file.write_bytes(palette)
 env={k:v for k,v in os.environ.items() if not k.startswith('NF_')}
 env.update(NF_ENDPOINT_COMMAND_CAMERAS=str(camera_file),NF_ENDPOINT_DISPLAY_PALETTE=str(palette_file),NF_CONTINUOUS_ROAD_UV='1',NF_ROAD_RECIPROCAL=str(p/'road-correction-reciprocal.bin'))
 def render(empty=False):
  e=dict(env)
  if empty:e['NF_ENDPOINT_COMMANDS']='4294967200'
  target=out/'result.ppm';subprocess.run([str(p/'sampled-scene-preview.exe'),str(packet),str(target)],env=e,capture_output=True,check=True)
  file=Path(str(target)+'-0.ppm')
  with Image.open(file) as im:assert im.size==(3840,2160);array=np.array(im)
  file.unlink();return array
 empty=render(True);scene=render();repeat=render();assert np.array_equal(scene,repeat)
 changed=np.any(scene!=empty,axis=2);assert changed.any()
 colors=np.frombuffer(palette,dtype='<u2').reshape(160,256)
 rgb=np.stack([((colors>>(k*5))&31)*255//31 for k in range(3)],axis=2).astype(np.uint8)
 invalid=0
 for y in range(2160):
  actual=scene[y][changed[y]]
  if not len(actual):continue
  bank=rgb[min(159,int(y/13.5))]
  pack=lambda a:(a[:,0].astype(np.uint32)<<16)|(a[:,1].astype(np.uint32)<<8)|a[:,2]
  invalid+=int((~np.isin(pack(actual),pack(bank))).sum())
 assert invalid==0,invalid
 if previous is not None:
  difference=int(np.any(scene!=previous,axis=2).sum());assert difference>0 and camera[24:]!=previous_cameras
  motion.append(dict(changed_pixels=difference,command_cameras_changed=True))
 checks.append(dict(target=proof['target'],repeat_exact=True,geometry_pixels=int(changed.sum()),invalid_palette_colors=invalid,packet_sha256=proof['packet_sha256']))
 Image.fromarray(scene).resize((960,540)).save(out/f'frame-{ordinal}.png')
 previous=scene;previous_cameras=camera[24:]
report=dict(result='PASS',checks=checks,motion=motion,output=str(out),scope='Three actual complete corrected-transition 4K GPU diagnostic scenes, repeated RGB exact, geometry RGB belongs owned display-row palette, adjacent cameras/images change. Captured live PNG hashes verified. Independent per-pixel index/UV/occlusion correctness, motion smoothness and fullscene60fps not proven.')
(p/'indexed-transition-gpu-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
Path(str(prefix)+'-indexed-gpu-audit.json').write_text(json.dumps(report,indent=2))
