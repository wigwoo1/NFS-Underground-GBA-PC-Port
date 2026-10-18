"""Native model GPU replay with real display palettes and immutable cameras."""
import json,os,struct,subprocess,uuid,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
p=Path(__file__).resolve().parent
prefix=p/'prototype-runs/threaded-prepared-2d9f8b417e1943be80cb86a65dc8f12d'
out=p/'prototype-runs'/('indexed-palette-scenes-'+uuid.uuid4().hex);out.mkdir()
checks=[]
for frame in (1,8,16):
    base=Path(str(prefix)+f'-dense-{frame:02}')
    packet=Path(str(base)+'-native-scene.bin')
    cameras=Path(str(base)+'-owned-cameras.bin').read_bytes()
    assert struct.unpack_from('<3I',cameras)==(0x5043464e,1,0)
    camera=out/f'{frame}-cameras.bin';camera.write_bytes(cameras[24:])
    hud=Path(str(base)+'-owned-hud.bin').read_bytes();assert len(hud)==160*34944
    raw=b''.join(hud[y*34944+32896:y*34944+32896+512] for y in range(160))
    palette=out/f'{frame}-palette.bin';palette.write_bytes(raw)
    env={k:v for k,v in os.environ.items() if not k.startswith('NF_')}
    env.update(NF_ENDPOINT_COMMAND_CAMERAS=str(camera),NF_ENDPOINT_COMMANDS='4294967295')
    env.update(NF_CONTINUOUS_ROAD_UV='1',NF_ROAD_RECIPROCAL=str(p/'road-correction-reciprocal.bin'))
    images=[]
    for label,enabled in (('baked',False),('display',True),('repeat',True)):
        e=dict(env)
        if enabled:e['NF_ENDPOINT_DISPLAY_PALETTE']=str(palette)
        target=out/f'{frame}-{label}.ppm'
        subprocess.run([str(p/'sampled-scene-preview.exe'),str(packet),str(target)],env=e,capture_output=True,check=True)
        images.append(np.array(Image.open(str(target)+'-0.ppm')))
    assert np.array_equal(images[1],images[2])
    colors=np.frombuffer(raw,dtype='<u2').reshape(160,256)
    rgb=np.stack([((colors>>(k*5))&31)*255//31 for k in range(3)],axis=2).astype(np.uint8)
    invalid=0
    for y in range(324,1944):
        row=int(y/13.5)
        actual=images[1][y,300:3513]
        allowed=rgb[row]
        packed=(actual[:,0].astype(np.uint32)<<16)|(actual[:,1].astype(np.uint32)<<8)|actual[:,2]
        bank=(allowed[:,0].astype(np.uint32)<<16)|(allowed[:,1].astype(np.uint32)<<8)|allowed[:,2]
        invalid+=int((~np.isin(packed,bank)).sum())
    assert invalid==0
    changed=int(np.any(images[0]!=images[1],axis=2).sum())
    assert changed>0
    Image.fromarray(images[1]).resize((960,540)).save(out/f'{frame}-display.png')
    checks.append(dict(frame=frame,packet_sha256=hashlib.sha256(packet.read_bytes()).hexdigest(),
        palette_sha256=hashlib.sha256(raw).hexdigest(),changed_vs_baked_pixels=changed,
        invalid_world_palette_colors=invalid,repeat_exact=True))
    # Readbacks are reproducible intermediates; retain compact review and inputs.
    for label in ('baked','display','repeat'):
        (out/f'{frame}-{label}.ppm-0.ppm').unlink()
report=dict(result='PASS',checks=checks,output=str(out),scope='Three actual native isolated model4K scenes, display palette membership and deterministic replay. No original model pixel correspondence, walls/road lighting, live integration or60fps proof.')
(p/'captured-indexed-palette-gpu-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
