"""Decode owned native packet world data; no screen-space correspondence."""
from pathlib import Path
import struct,json,sys,hashlib,math
from PIL import Image,ImageDraw
packet=Path(sys.argv[1]);out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True);b=packet.read_bytes()
def words(data,at,count):return struct.unpack_from('<'+'I'*count,data,at)
h=words(b,0,8);assert h[0]==0x3150534e and h[2]==len(b) and h[3]==5
sections=[]
for i in range(5):
 tag,offset,size=words(b,32+12*i,3);assert tag==i+1 and offset+size<=len(b);sections.append(b[offset:offset+size])
w=sections[1];assert words(w,0,1)[0]==0x31444652;count=words(w,4,1)[0];pos=8;surfaces=[];textures=[]
for i in range(count):
 n,width,height=words(w,pos,3);pos+=12;assert 3<=n<=32 and 0<width<=1024 and 0<height<=1024
 vertices=[struct.unpack_from('<ddd',w,pos+j*24) for j in range(n)];pos+=n*24
 uv=[struct.unpack_from('<dd',w,pos+j*16) for j in range(n)];pos+=n*16
 assert all(math.isfinite(v) for row in vertices+uv for v in row)
 rgba=w[pos:pos+width*height*4];pos+=width*height*4;assert len(rgba)==width*height*4
 identity=words(sections[4],8+i*20,5)
 surfaces.append(dict(index=i,kind=identity[0],state=hex(identity[1]),source=hex(identity[2]),base=hex(identity[3]),vertices=vertices,uv=uv,texture_size=[width,height],texture_sha256=hashlib.sha256(rgba).hexdigest()))
 textures.append(Image.frombytes('RGBA',(width,height),rgba).convert('RGB'))
assert words(w,pos,2)==(0x3149574e,count);pos+=8
for s in surfaces:
 mode,size=words(w,pos,2);pos+=8;payload=w[pos:pos+size];pos+=size
 s.update(metadata_mode=mode,metadata_bytes=size,metadata_sha256=hashlib.sha256(payload).hexdigest())
 if mode in (2,3):s['wall_state_counts']={str(k):payload.count(k) for k in (0,1,2)}
assert pos==len(w)
ids=sections[4];trailer=8+words(ids,4,1)[0]*20
if len(ids)>trailer:
 assert words(ids,trailer,2)==(0x3142464e,count)
 for i,s in enumerate(surfaces):s['sampled_bounds']=struct.unpack_from('<HHHH',ids,trailer+16+i*8)
wall=[(s,im) for s,im in zip(surfaces,textures) if s['kind']==2]
canvas=Image.new('RGB',(800,200*math.ceil(len(wall)/4)), '#161616');d=ImageDraw.Draw(canvas)
for k,(s,im) in enumerate(wall):
 x=k%4*200;y=k//4*200;im.thumbnail((190,165));canvas.paste(im,(x,y+28));d.text((x+3,y+3),f"wall {s['index']} mode {s['metadata_mode']} {s['state']}",fill='white')
canvas.save(out/'native-wall-textures.png')
report=dict(result='DECODED',packet_sha256=hashlib.sha256(b).hexdigest(),serial=h[4],begin=h[5],end=h[6],surface_count=count,wall_count=len(wall),surfaces=surfaces,scope='Owned world vertices, materials, identities, writer states and sampled bounds. Does not prove original world recovery or visibility fidelity.')
(out/'native-world-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='surfaces'},indent=2))
