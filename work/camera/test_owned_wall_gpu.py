from pathlib import Path
import subprocess,json,hashlib,struct,math,os
import numpy as np
from PIL import Image
p=Path('work/camera');checks=[]
reference=json.loads((p/'motion-model-face-dispatch-tests.json').read_text())['draws']
models=[m for scene in json.loads((p/'motion-model-snapshots.json').read_text())['scenes'] for m in scene['models']]
assert len(models)==7

for scene_index,refresh in enumerate((8758,8762,8766,8769,8773,8776,8780)):
 out=p/f'owned-wall-textured-{refresh}.ppm';ledger=p/f'owned-model-gpu-faces-{refresh}.bin'
 run=subprocess.run([str((p/'owned-wall-gpu-preview.exe').resolve()),str(p/f'motion-actual-scanline-assets/{refresh}-model-sources.bin'),str(out)],capture_output=True,text=True,env={**os.environ,'NF_GPU_FACE_LEDGER':str(ledger.resolve())})
 assert run.returncode==0,(refresh,run.stdout,run.stderr)
 raw=ledger.read_bytes();offset=0;actual=[]
 while offset<len(raw):
  context,face,count=struct.unpack_from('<3I',raw,offset);offset+=12;vertices=list(struct.unpack_from('<'+'H'*count,raw,offset));offset+=count*2;assert vertices==models[scene_index]['faces'][face]['vertices'];assert context==models[scene_index]['context_address'];actual.append(face)
 expected=next(draw['dispatched_faces'] for draw in reference if draw['event']==models[scene_index]['event']);assert actual==expected,(refresh,actual,expected)
 im=Image.open(out);assert im.size==(3840,2160);assert len(im.getcolors(3840*2160))>100
 checks.append(dict(refresh=refresh,exact_original_model_faces=actual,result=run.stdout.strip(),rgb_sha256=hashlib.sha256(im.tobytes()).hexdigest()))
raw=bytearray((p/'motion-actual-scanline-assets/8758-model-sources.bin').read_bytes());offset=0
while offset<len(raw):
 magic,kind,context,count=struct.unpack_from('<4I',raw,offset);offset+=16
 for i in range(count):
  size=struct.unpack_from('<I',raw,offset)[0];offset+=4
  if kind in (1,2) and i==5:struct.pack_into('<4H',raw,offset,80,160,40,120)
  if kind==3 and i==9:struct.pack_into('<4i',raw,offset,80,40,161,121)
  offset+=size
packet=p/'owned-wall-scissor-test.bin';packet.write_bytes(raw);output=p/'owned-wall-scissor-test.ppm'
run=subprocess.run([str((p/'owned-wall-gpu-preview.exe').resolve()),str(packet),str(output)],capture_output=True,text=True);assert run.returncode==0,run.stderr
image=np.asarray(Image.open(output));background=image[0,0];changed=np.any(image!=background,axis=2)
x0=1380;x1=2474;y0=540;y1=1634
outside=changed.copy();outside[y0:y1,x0:x1]=False
assert not outside.any();assert changed.sum()>1000
scissor=dict(result='PASS_ALL_WORLD_GPU_RESTRICTED_SCISSOR',changed_pixels=int(changed.sum()),outside_writes=int(outside.sum()))
r=dict(result='PASS_OWNED_WALL_TEXTURE_GPU_4K',checks=checks,scissor=scissor,scope='Seven offscreen captured scenes, owned world endpoints/material/texture/palette, near-clipped perspective UVs. Default UV mode; native scissor verified by restricted rectangle; no shading/original-pixel material parity or complete scene/motion/playability proof.')
(p/'owned-wall-textured-gpu-tests.json').write_text(json.dumps(r,indent=2));print(r)
