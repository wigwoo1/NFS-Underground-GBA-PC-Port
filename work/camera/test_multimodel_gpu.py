from pathlib import Path
import struct, subprocess, os, hashlib, json
root=Path('work/camera').resolve(); fixture=next((root/'packet-sequence').glob('scene-*.packet')).read_bytes()
def section(i):
 off,size=struct.unpack_from('<2I',fixture,36+i*12);return fixture[off:off+size]
model=section(0); lighting=section(3); table=lighting[-131072:]; identity=section(4)[-20:]
def packet(models,order,serial,end):
 if len(models)==1: model_data=models[0]
 else:
  model_data=bytearray(struct.pack('<2I',0x314c4d4e,len(models))+bytes(len(models)*8))
  for i,m in enumerate(models):
   model_data.extend(bytes((-len(model_data))%8));offset=len(model_data);struct.pack_into('<2I',model_data,8+i*8,offset,len(m));model_data.extend(m)
 ids=bytearray(struct.pack('<2I',0x3149464e,len(models)))
 for i in range(len(models)):
  row=bytearray(identity);struct.pack_into('<I',row,8,0x02000000+i*164);ids.extend(row)
 sections=[model_data,struct.pack('<2I',0x31444652,0),struct.pack('<2I',0x314f464e,len(models))+struct.pack(f'<{len(models)}I',*order),struct.pack('<2I',0x314c464e,0)+table,ids]
 raw=bytearray(96);struct.pack_into('<8I',raw,0,0x3150534e,1 if len(models)==1 else 2,0,5,serial,end-1,end,0)
 for i,s in enumerate(sections):
  raw.extend(bytes((-len(raw))%8));struct.pack_into('<3I',raw,32+i*12,i+1,len(raw),len(s));raw.extend(s)
 struct.pack_into('<I',raw,8,len(raw));return raw
red=bytearray(model);width,height=struct.unpack_from('<2I',model,16);start=len(model)-width*height*4
for i in range(start,len(model),4): red[i:i+3]=bytes((240,30,70))
def render(name,models,order,newer=None):
 a=root/f'multi-gpu-{name}-a.packet';b=root/f'multi-gpu-{name}-b.packet';prefix=root/f'multi-gpu-{name}'
 a.write_bytes(packet(models,order,100,100));b.write_bytes(packet(models if newer is None else newer,order,101,104))
 env=dict(os.environ,NF_PREVIEW_PHASE='2');subprocess.run([str(root/'multimodel-preview.exe'),str(a),str(b),str(prefix)],env=env,check=True,capture_output=True)
 data=Path(str(prefix)+'-2.ppm').read_bytes();assert data.startswith(b'P6\n3840 2160\n255\n');return data
original=render('single-original',[model],[0xffffffff]);colored=render('single-red',[red],[0xffffffff]);assert original!=colored
last_original=render('last-original',[model,red],[0xfffffffe,0xffffffff])
last_red=render('last-red',[model,red],[0xffffffff,0xfffffffe])
assert last_original==original and last_red==colored
shifted=bytearray(red);x=struct.unpack_from('<d',shifted,104)[0];struct.pack_into('<d',shifted,104,x+100)
moved=render('distinct-pose',[model,shifted],[0xffffffff,0xfffffffe]);assert moved not in (original,colored,last_red)
future=bytearray(red);struct.pack_into('<d',future,104,x+200)
midpoint=render('independent-midpoint',[model,red],[0xffffffff,0xfffffffe],[model,future]);assert midpoint==moved
report={'result':'PASS','exact_4k_rgb_pixels':3*3840*2160,'interleaved_model_order_and_independent_textures':True,'distinct_second_pose_changes_frame':True,'independent_second_pose_midpoint_exact':True,'hashes':{k:hashlib.sha256(v).hexdigest() for k,v in [('original',original),('colored',colored),('moved',moved)]},'scope':'Offscreen packet GPU replay; identical overlapping geometry proves last-command material/order; shifted second pose and independent midpoint verified. Live multi-car generation and full-scene timing remain pending.'}
(root/'multimodel-gpu-tests.json').write_text(json.dumps(report,indent=2));print(report)
