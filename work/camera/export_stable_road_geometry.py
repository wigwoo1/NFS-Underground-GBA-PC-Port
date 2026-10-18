"""Export validated retained road geometry for source-based UV investigation."""
from pathlib import Path
import struct,json,hashlib,ctypes as C,math
p=Path('work/camera');source=p/'prototype-runs/racing-motion-audit-a88232ac136d4ad58dc7231b706de812-complete-stable-bundle.bin';b=source.read_bytes();h=struct.unpack_from('<8I',b);ordered=b[h[5]:h[5]+h[6]];oh=struct.unpack_from('<16I',ordered);packet=ordered[oh[12]:oh[12]+oh[13]];sections={tag:packet[off:off+size] for tag,off,size in [struct.unpack_from('<3I',packet,32+12*i) for i in range(5)]};world=sections[2];magic,count=struct.unpack_from('<2I',world);assert magic==0x31444652
surfaces=[];pos=8
for i in range(count):
 n,w,ht=struct.unpack_from('<3I',world,pos);size=12+n*40+w*ht*4;raw=world[pos:pos+size];assert len(raw)==size
 vertices=[struct.unpack_from('<3d',raw,12+j*24) for j in range(n)];uv=[struct.unpack_from('<2d',raw,12+n*24+j*16) for j in range(n)];assert all(math.isfinite(v) for row in vertices+uv for v in row)
 surfaces.append(dict(surface=i,width=w,height=ht,vertices=vertices,uv=uv,raw=raw));pos+=size
assert struct.unpack_from('<2I',world,pos)==(0x3149574e,count);pos+=8;roads=[]
class Section(C.Structure):_fields_=[('data',C.c_void_p),('size',C.c_size_t)]
d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));fn=d.nf_scene_road_attributes_match;fn.argtypes=[Section,C.c_void_p];fn.restype=C.c_int
for item in surfaces:
 mode,length=struct.unpack_from('<2I',world,pos);pos+=8;payload=world[pos:pos+length];assert len(payload)==length;pos+=length
 if mode not in (5,6):continue
 raw=payload[-288:];attrs=struct.unpack('<6I66i',raw);assert len(payload)==item['width']*item['height']+288
 geometry=C.create_string_buffer(item['raw']);assert fn(Section(C.cast(geometry,C.c_void_p),len(item['raw'])),raw)
 item.pop('raw');item.update(mapping_mode=mode,source_attributes_header=attrs[:8],source_attributes=[attrs[8+j*2:10+j*2] for j in range(attrs[0])],indices_sha256=hashlib.sha256(payload[:-288]).hexdigest());roads.append(item)
assert pos==len(world) and roads
report=dict(result='PASS',serial=h[2],roads=roads,cameras=[struct.unpack_from('<7d',ordered,oh[11]+i*56) for i in range(oh[8])],order=list(struct.unpack_from('<'+str((len(sections[3])-8)//4)+'I',sections[3],8)),source_sha256=hashlib.sha256(b).hexdigest(),scope='Owned world geometry, rawUV attributes, mapping modes, ordered cameras/order exported; every road passes current native attribute-matching validator. No screen polygon correspondence, no GPU raster/UV parity claim.')
(p/'stable-road-geometric-inputs.json').write_text(json.dumps(report,indent=2));print(dict(result='PASS',roads=len(roads),vertices=sum(len(r['vertices']) for r in roads),cameras=len(report['cameras']),source_sha256=report['source_sha256']))
