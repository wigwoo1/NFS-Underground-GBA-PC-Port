"""Synthetic corrected attributes on captured geometry; preserve historical layers/order."""
from pathlib import Path
import argparse,hashlib,json,math,struct
p=argparse.ArgumentParser()
for n in ('input','output','table'):p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);raw=a.input.read_bytes();chunks=[]
for i in range(4):at,size=struct.unpack_from('<QQ',raw,64+i*16);chunks.append(raw[at:at+size])
packet=chunks[0];parts=[]
for i in range(5):at,size=struct.unpack_from('<II',packet,36+i*12);parts.append(packet[at:at+size])
world=parts[1];count=struct.unpack_from('<I',world,4)[0];at=8;surfaces=[]
for i in range(count):
 n,w,h=struct.unpack_from('<III',world,at);size=12+n*40+w*h*4;surfaces.append(bytearray(world[at:at+size]));at+=size
assert struct.unpack_from('<II',world,at)==(0x3149574e,count);at+=8;metadata=[]
for i in range(count):mode,size=struct.unpack_from('<II',world,at);at+=8;metadata.append((mode,world[at:at+size]));at+=size
assert at==len(world);table=a.table.read_bytes();assert len(table)==131072;manifest={}
for corrected_mode in (5,6):
 new=[];metas=[];roads=0
 for i,surface in enumerate(surfaces):
  surface=surface.copy();mode,data=metadata[i];kind=struct.unpack_from('<I',parts[4],8+i*20)[0]
  if kind==1:
   assert mode==1;n,w,h=struct.unpack_from('<III',surface);shift=w.bit_length()-1;assert 1<<shift==w;attributes=bytearray(288);struct.pack_into('<6I2i',attributes,0,n,shift,h*2,corrected_mode==6,0x08001000,0x02000002,0,0)
   for j in range(n):
    u,v=struct.unpack_from('<dd',surface,12+n*24+j*16);x,y=round(u*16384),round(v*16384);struct.pack_into('<ii',attributes,32+j*8,x,y);struct.pack_into('<dd',surface,12+n*24+j*16,x/16384,y/16384)
   data+=attributes;mode=corrected_mode;roads+=1
  new.append(surface);metas.append(struct.pack('<II',mode,len(data))+data)
 assert roads==3;modified=parts.copy();modified[1]=struct.pack('<II',0x31444652,count)+b''.join(new)+struct.pack('<II',0x3149574e,count)+b''.join(metas);modified[3]=parts[3][:-131072]+table;geometry=bytearray(packet[:92])
 for i,part in enumerate(modified):struct.pack_into('<II',geometry,36+i*12,len(geometry),len(part));geometry+=part
 struct.pack_into('<I',geometry,8,len(geometry));bundle=bytearray(raw[:128])
 for i,chunk in enumerate([geometry]+chunks[1:]):struct.pack_into('<QQ',bundle,64+i*16,len(bundle),len(chunk));bundle+=chunk
 struct.pack_into('<Q',bundle,16,len(bundle));name=f'mode{corrected_mode}.nab';(a.output/name).write_bytes(bundle);manifest[name]={'sha256':hashlib.sha256(bundle).hexdigest(),'corrected_roads':roads,'synthetic_raw_attributes':True,'captured_geometry':True,'source_order_preserved':True,'scope':'Shared-camera corrected path; not original endpoint source-ring projection'}
(a.output/'fixture-manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
