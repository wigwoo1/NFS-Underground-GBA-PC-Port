"""Regenerated model geometry/texture and sampled-camera 4K diagnostic."""
from pathlib import Path
import json,struct,hashlib,subprocess,os,sys,math
from PIL import Image,ImageChops
p=Path('work/camera').resolve();f=p/'overflow-scene-171';old=(f/'old.bin').read_bytes();new=(f/'new.bin').read_bytes()
sections={t:(o,n) for t,o,n in (struct.unpack_from('<3I',old,32+i*12) for i in range(5))}
offset,size=sections[1];captured=old[offset:offset+size];world_count=struct.unpack_from('<I',old,sections[2][0]+4)[0];identities=old[sections[5][0]+8:sections[5][0]+8+world_count*20]
motion=len(sys.argv)>1 and sys.argv[1]=='motion';suffix='-motion' if motion else '';cases=[];hashes=[]
new_model=next(new[o:o+n] for tag,o,n in (struct.unpack_from('<3I',new,32+i*12) for i in range(5)) if tag==1)
for alpha in ('0.25','0.5','0.75'):
 model=(p/f'sampled-model-{alpha}{suffix}.bin').read_bytes();assert len(model)==size
 # Entire topology, local positions, UVs and exact draw-palette texture match.
 assert model[:24]==captured[:24] and model[160:]==captured[160:]
 pose=(p/f'visibility-overflow-171-wide/pose-{alpha}.bin').read_bytes();view=struct.unpack_from('<12i',pose,56)
 assert struct.unpack_from('<3d',model,48)==tuple(-v for v in view[9:12])
 if not motion:assert model[104:160]==captured[104:160]
 else:
  t=float(alpha);a_pose=struct.unpack_from('<7d',captured,104);b_pose=struct.unpack_from('<7d',new_model,104);actual=struct.unpack_from('<7d',model,104)
  assert all(abs(actual[i]-((1-t)*a_pose[i]+t*b_pose[i]))<=1/512+1e-8 for i in range(3))
  qa=list(a_pose[3:]);qb=list(b_pose[3:]);dot=sum(x*y for x,y in zip(qa,qb))
  if dot<0:qb=[-v for v in qb];dot=-dot
  theta=math.acos(min(dot,1));weights=(1-t,t) if dot>=.9995 else (math.sin((1-t)*theta)/math.sin(theta),math.sin(t*theta)/math.sin(theta))
  q=[weights[0]*x+weights[1]*y for x,y in zip(qa,qb)];length=math.sqrt(sum(v*v for v in q));q=[v/length for v in q]
  assert abs(sum(x*y for x,y in zip(q,actual[3:])))>1-1e-8
 packet=bytearray(old);packet[offset:offset+size]=model;second=bytearray(packet);second[16:32]=new[16:32]
 a=f/f'sampled-model-{alpha}{suffix}-a.bin';b=f/f'sampled-model-{alpha}{suffix}-b.bin';a.write_bytes(packet);b.write_bytes(second)
 header=struct.unpack_from('<8I',packet);clips=struct.pack('<5Id',0x3150434e,*header[4:7],world_count,float(alpha))
 for i in range(world_count):clips+=identities[i*20:i*20+20]+struct.pack('<4H',0,240,0,160)
 clip=f/f'sampled-model-{alpha}{suffix}.clips';clip.write_bytes(clips);env=os.environ.copy();env.update(NF_CAPTURE_CLIPS=str(clip),NF_PREVIEW_FRACTION=alpha,NF_PREVIEW_PHASE='2')
 images=[]
 for only in (999,4294967295):
  env['NF_ONLY_SURFACE']=str(only);prefix=f/f'sampled-model-{alpha}{suffix}-{only}'
  subprocess.run([str(p/'isolated-clip-preview.exe'),str(a),str(b),str(prefix)],check=True,capture_output=True,env=env)
  with Image.open(str(prefix)+'-2.ppm') as im:assert im.size==(3840,2160);images.append(im.convert('RGB'))
 diff=ImageChops.difference(*images);pixels=sum(v!=(0,0,0) for v in diff.get_flattened_data());assert pixels>0
 hashes.append(hashlib.sha256(images[1].tobytes()).hexdigest());cases.append(dict(alpha=float(alpha),pixels=pixels,bbox=diff.getbbox(),camera_position=list(struct.unpack_from('<3d',model,48))))
assert len(set(hashes))==3
report=dict(object_motion=motion,result='PASS',bytes=size,vertices=struct.unpack_from('<I',captured,4)[0],faces=struct.unpack_from('<I',captured,8)[0],geometry_uv_texture_exact=True,cases=cases,scope=('Native regenerated model with sampled camera/context and interpolated object pose' if motion else 'Sampled camera with frozen earlier object pose')+'; isolated frozen-pair 4K diagnostic. Original endpoint region/object linked lists retained. Full scene, live presentation and gameplay timing unverified.')
(p/f'sampled-model-render{suffix}-tests.json').write_text(json.dumps(report,indent=2));print(report)
