from pathlib import Path
import struct,json
from owned_portal_transform import transform,project_edge
from owned_partition_bounds import record
p=Path('work/camera');raw=(p/'owned-traversals.bin').read_bytes();rb=(p/'road-correction-reciprocal.bin').read_bytes();table=struct.unpack('<'+str(len(rb)//4)+'I',rb);offset=0;pending=None;checks=[]
while offset<len(raw):
 h=struct.unpack_from('<12I',raw,offset);offset+=48;assert h[0]==0x3156544e
 if h[1]==1:
  n=432+h[9]*68;payload=raw[offset:offset+n];offset+=n;pending=(h,payload)
 else:
  expected=raw[offset:offset+h[5]];offset+=h[5];a,payload=pending;assert a[3]==h[3]
  state=payload[:256];matrix=struct.unpack_from('<12i',payload,304);fb=payload[352:416];parent=struct.unpack_from('<8H',payload,416);points=payload[432:];out=[]
  near=struct.unpack_from('<i',fb,16)[0];scale=struct.unpack_from('<I',fb,28)[0];center=struct.unpack_from('<h',fb,8)[0]
  for i in range(a[9]):
   point=points[i*68:(i+1)*68];descriptor=struct.unpack_from('<H',point,48)[0]
   if descriptor==65535:continue
   nextpoint=points[((i+1)%a[9])*68:((i+1)%a[9])*68+68]
   x=transform(*struct.unpack_from('<2i',point),matrix);y=transform(*struct.unpack_from('<2i',nextpoint),matrix)
   if max(x[1],y[1])>0x6000:break
   edge=project_edge(x,y,near,scale,center,table,bool(a[8]))
   if edge is None:continue
   left,right,flags,z,nz=edge
   if left>=right or right<parent[1] or left>=parent[2]:continue
   out.append(record(descriptor,left,right,flags,parent,struct.unpack_from('<H',state,92)[0],struct.unpack_from('<H',state,94)[0],struct.unpack_from('<H',point,46)[0],z,nz))
  actual=[struct.unpack_from('<8H',expected,i*16)[:7] for i in range(h[4])]
  assert out==actual,(a[3],out,actual)
  checks.append(dict(refresh=a[2],sequence=a[3],candidates=a[9],outputs=len(out)))
assert checks
r=dict(result='PASS_RAW_PARENT_TRAVERSAL',calls=len(checks),outputs=sum(x['outputs'] for x in checks),checks=checks,scope='Full candidate order and rejection within each captured parent; outer root/hierarchy scheduling remains original.')
(p/'owned-traversal-tests.json').write_text(json.dumps(r,indent=2));print(r['result'],r['calls'],r['outputs'])
