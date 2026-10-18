"""Experimental enriched-road consumer on complete captured 4K scene."""
from pathlib import Path
import ctypes as C,struct,json,sys,runpy,subprocess,os,hashlib
from PIL import Image,ImageChops
p=Path('work/camera').resolve();sys.path.insert(0,str(p));sys.argv=['oracle','0.5','motion','road-full'];n=runpy.run_path(str(p/'test_sampled_object_dispatch.py'));d=n['d'];P=C.c_void_p;Z=C.c_size_t;U=C.c_uint
class Section(C.Structure):_fields_=[('data',P),('size',Z)]
class Attributes(C.Structure):_fields_=[('count',U),('shift',U),('stored_height',U),('affine',U),('material',U),('animation',U),('offsets',C.c_int32*2),('attributes',(C.c_int32*2)*32)]
extract=d.nf_scene_command_road_attributes_owned;extract.argtypes=[P,n['Read'],P,P]
attach=d.nf_scene_world_attach_road_attributes;attach.argtypes=[Section,U,P,Z,P,C.POINTER(P),C.POINTER(Z)]
mapping=d.nf_scene_world_road_mapping;mapping.argtypes=[Section,U,C.POINTER(P),C.POINTER(Z),C.POINTER(U)];d.nf_scene_packet_free.argtypes=[P]
original=(p/'classified-command-scene.packet').read_bytes();parts=[]
for i in range(5):
 off,size=struct.unpack_from('<2I',original,36+i*12);parts.append(original[off:off+size])
world=parts[1];world_count=struct.unpack_from('<I',world,4)[0];roads=0
for i in range(world_count):
 kind,state,source,base,reserved=struct.unpack_from('<5I',parts[4],8+i*20)
 if kind!=1:continue
 command=next(c for c in n['commands'] if c.kind==1 and c.source==source);attrs=Attributes();assert extract(C.byref(command),n['immutable_reader'],None,C.byref(attrs))
 wb=C.create_string_buffer(world);section=Section(C.addressof(wb),len(world));ptr=P();size=Z();flag=U();assert mapping(section,i,C.byref(ptr),C.byref(size),C.byref(flag)) and flag.value==attrs.affine
 owned=P();length=Z();assert attach(section,i,ptr,size.value,C.byref(attrs),C.byref(owned),C.byref(length))
 world=C.string_at(owned,length.value);d.nf_scene_packet_free(owned);roads+=1
assert roads==10
parts[1]=world;enriched=bytearray(original[:96])
for i,part in enumerate(parts):
 enriched.extend(bytes((-len(enriched))%8));struct.pack_into('<2I',enriched,36+i*12,len(enriched),len(part));enriched.extend(part)
struct.pack_into('<I',enriched,8,len(enriched));enriched=bytes(enriched)
def later(raw):
 out=bytearray(raw);serial,begin,end=struct.unpack_from('<3I',out,16);struct.pack_into('<3I',out,16,serial+1,end+1,end+4);return bytes(out)
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=p/'road-correction-reciprocal.bin';table.write_bytes(rom[0x627700:0x647700]);env=os.environ.copy();env['NF_ROAD_RECIPROCAL']=str(table)
images=[];cases=[]
for name,raw in [('legacy',original),('corrected',enriched)]:
 a=p/f'road-attribute-{name}.packet';b=p/f'road-attribute-{name}-next.packet';a.write_bytes(raw);b.write_bytes(later(raw));prefix=p/f'road-attribute-{name}'
 result=subprocess.run([str(p/'road-attribute-preview.exe'),str(a),str(b),str(prefix)],env=env,capture_output=True,text=True)
 assert result.returncode==0,(name,result.returncode,result.stdout,result.stderr)
 with Image.open(str(prefix)+'-2.ppm') as im:
  assert im.size==(3840,2160);image=im.convert('RGB');images.append(image.copy());background=image.getpixel((0,0));covered=sum(v!=background for v in image.get_flattened_data());assert covered>1000000
  cases.append(dict(name=name,nonbackground_pixels=covered,image_sha256=hashlib.sha256(image.tobytes()).hexdigest()))
difference=ImageChops.difference(*images);changed=sum(v!=(0,0,0) for v in difference.get_flattened_data());assert changed>0
# Missing retained reciprocal input must reject enriched records before render.
missing=os.environ.copy();missing.pop('NF_ROAD_RECIPROCAL',None)
a=p/'road-attribute-corrected.packet';b=p/'road-attribute-corrected-next.packet'
r=subprocess.run([str(p/'road-attribute-preview.exe'),str(a),str(b),str(p/'road-attribute-missing')],env=missing,capture_output=True,text=True);assert r.returncode==41
# A valid different affine policy in the newer packet must reject the pair.
bad=bytearray(later(enriched));world_off,world_size=struct.unpack_from('<2I',bad,48);cursor=world_off+8
for _ in range(world_count):
 count,w,h=struct.unpack_from('<3I',bad,cursor);cursor+=12+count*40+w*h*4
cursor+=8;mode,length=struct.unpack_from('<2I',bad,cursor);assert mode in (5,6)
struct.pack_into('<I',bad,cursor,11-mode);struct.pack_into('<I',bad,cursor+8+length-288+12,int(mode==5))
policy_path=p/'road-attribute-changed-policy.packet';policy_path.write_bytes(bad)
r=subprocess.run([str(p/'road-attribute-preview.exe'),str(a),str(policy_path),str(p/'road-attribute-rejected')],env=env,capture_output=True,text=True);assert r.returncode==43,(r.returncode,r.stdout,r.stderr)
report=dict(result='PASS',changed_policy_pair_rejection=43,enriched_roads=roads,cases=cases,changed_pixels=changed,missing_reciprocal_rejection=41,scope='One full captured acquired-pair scene rendered4K with source UV correction on all10roads; geometry clipping remains continuous. Image difference demonstrates active path, not original GPU pixel parity, motion timing or live integration. Identical poses with later packet header; bilinear correction is experimental policy.')
(p/'road-attribute-gpu-tests.json').write_text(json.dumps(report,indent=2));print(report)
