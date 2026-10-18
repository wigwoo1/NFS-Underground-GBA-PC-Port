"""Actual wall GPU support and display palette membership; bounded artifacts."""
import json,os,struct,subprocess,uuid,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
p=Path(__file__).resolve().parent
prefix=p/'prototype-runs/threaded-prepared-c90ce62f38a7417d898be3c380f9fe3a'
base=Path(str(prefix)+'-dense-01');packet=Path(str(base)+'-native-scene.bin');raw=packet.read_bytes()
provenance=json.loads(Path(str(prefix)+'-sampled-provenance.json').read_text());assert provenance['result']=='PASS'
assert provenance['checks'][0]['packet_sha256']==hashlib.sha256(raw).hexdigest()
out=p/'prototype-runs'/('wall-palette-audit-'+uuid.uuid4().hex);out.mkdir()
camera=Path(str(base)+'-owned-cameras.bin').read_bytes();assert struct.unpack_from('<3I',camera)==(0x5043464e,1,0)
camera_file=out/'cameras.bin';camera_file.write_bytes(camera[24:])
hud=Path(str(base)+'-owned-hud.bin').read_bytes();assert len(hud)==160*34944
palette=b''.join(hud[y*34944+32896:y*34944+32896+512] for y in range(160));palette_file=out/'palette.bin';palette_file.write_bytes(palette)
env={k:v for k,v in os.environ.items() if not k.startswith('NF_')}
env.update(NF_ENDPOINT_COMMAND_CAMERAS=str(camera_file),NF_CONTINUOUS_ROAD_UV='1',NF_ROAD_RECIPROCAL=str(p/'road-correction-reciprocal.bin'))
target=out/'result.ppm'
rejected=subprocess.run([str(p/'sampled-scene-preview.exe'),str(packet),str(target)],env=env,capture_output=True)
assert rejected.returncode==43 and not Path(str(target)+'-0.ppm').exists()
sections={t:raw[o:o+n] for t,o,n in (struct.unpack_from('<3I',raw,32+j*12) for j in range(5))}
ids=sections[5];count=struct.unpack_from('<I',ids,4)[0];wall=next(j for j in range(count) if struct.unpack_from('<I',ids,8+j*20)[0]==2)
at=8+count*20;assert ids[at:at+4]==b'NFB2';left,right,top,bottom=struct.unpack_from('<4H',ids,at+16+wall*8)
left=left//2*2;right=min(240,right//2*2+2);bottom=min(160,bottom+2)
def render(command):
 e=dict(env,NF_ENDPOINT_DISPLAY_PALETTE=str(palette_file),NF_ENDPOINT_COMMANDS=str(command))
 subprocess.run([str(p/'sampled-scene-preview.exe'),str(packet),str(target)],env=e,capture_output=True,check=True)
 file=Path(str(target)+'-0.ppm')
 with Image.open(file) as im:array=np.array(im)
 file.unlink();return array
empty=render(4294967200);image=render(wall);repeat=render(wall);assert np.array_equal(image,repeat)
changed=np.any(image!=empty,axis=2)
x0,x1,y0,y1=[int(np.ceil(v-.5)) for v in (300+left*13.5,300+right*13.5,top*13.5,bottom*13.5)]
inside=np.zeros(changed.shape,bool);inside[y0:y1,x0:x1]=True
assert not np.any(changed&~inside) and changed.any()
colors=np.frombuffer(palette,dtype='<u2').reshape(160,256)
rgb=np.stack([((colors>>(k*5))&31)*255//31 for k in range(3)],axis=2).astype(np.uint8)
invalid=0
for y in range(2160):
 actual=image[y][changed[y]]
 if not len(actual):continue
 row=int(y/13.5);bank=rgb[row]
 packed=(actual[:,0].astype(np.uint32)<<16)|(actual[:,1].astype(np.uint32)<<8)|actual[:,2]
 allowed=(bank[:,0].astype(np.uint32)<<16)|(bank[:,1].astype(np.uint32)<<8)|bank[:,2]
 invalid+=int((~np.isin(packed,allowed)).sum())
assert invalid==0
Image.fromarray(image).resize((960,540)).save(out/'review.png')
report=dict(result='PASS',wall=wall,changed_pixels=int(changed.sum()),outside_support=0,invalid_display_colors=invalid,
    missing_palette_rejected=True,repeat_exact=True,output=str(out),scope='One actual owned wall native4K replay/displaypalette membership/portal. Independent outputindex/UV/shade correspondence andfullscene60fps notproven.')
(p/'owned-wall-palette-gpu-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
