"""Explicit ownership sentinels on validated split-page provenance; not game artwork."""
from pathlib import Path
import argparse,struct,hashlib,json
p=argparse.ArgumentParser()
for n in ('split','mesh_packet','output'):p.add_argument('--'+n.replace('_','-'),type=Path,required=True)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);raw=a.split.read_bytes();chunks=[]
for i in range(4):at,size=struct.unpack_from('<QQ',raw,64+i*16);chunks.append(raw[at:at+size])
packet=a.mesh_packet.read_bytes();parts=[]
for i in range(5):at,size=struct.unpack_from('<II',packet,36+i*12);parts.append(packet[at:at+size])
manifest={};(a.output/'captured-split.nab').write_bytes(raw);manifest['captured-split.nab']={'sha256':hashlib.sha256(raw).hexdigest(),'synthetic_sentinel':False,'split_row':struct.unpack_from('<Q',raw,48)[0]}
for cut in (1,79,80,81,159):
 geometry=[];layer=bytearray(chunks[2]);provenance=bytearray(chunks[3])
 for owner in range(2):
  color=(211,37,19,255) if owner==0 else (17,61,227,255);points=[(-120,-80,100),(120,-80,100),(120,80,100),(-120,80,100)];surface=struct.pack('<3I',4,2,2)+b''.join(struct.pack('<3d',*v) for v in points)+struct.pack('<8d',*([.25,.25]*4))+bytes(color)*4;modified=parts.copy();modified[1]=struct.pack('<2I',0x31444652,1)+surface+struct.pack('<4I',0x3149574e,1,0,0);new=bytearray(chunks[owner][:92])
  for i,part in enumerate(modified):struct.pack_into('<II',new,36+i*12,len(new),len(part));new+=part
  struct.pack_into('<I',new,8,len(new));geometry.append(new)
 for y in range(160):
  owner=0 if y<cut else 1;owner_at=(8+owner*8)*8;page=struct.unpack_from('<Q',provenance,owner_at+32)[0];generation=struct.unpack_from('<Q',provenance,owner_at+40)[0];control=struct.unpack_from('<H',layer,32+y*128+8)[0];control=(control&~(0x8080|0x10|7))|4|(page<<4);struct.pack_into('<H',layer,32+y*128+8,control);row=(24+y*4)*8;struct.pack_into('<Q',provenance,row,control);struct.pack_into('<Q',provenance,row+8+page*8,generation)
 bundle=bytearray(raw[:128]);struct.pack_into('<Q',bundle,48,cut)
 for i,part in enumerate(geometry+[layer,provenance]):struct.pack_into('<QQ',bundle,64+i*16,len(bundle),len(part));bundle+=part
 struct.pack_into('<Q',bundle,16,len(bundle));name=f'sentinel-{cut}.nab';(a.output/name).write_bytes(bundle);manifest[name]={'sha256':hashlib.sha256(bundle).hexdigest(),'split_row':cut,'synthetic_sentinel':True,'owner_colors':[[211,37,19],[17,61,227]],'source_ownership_metadata_explicitly_modified':True}
(a.output/'fixture-manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
