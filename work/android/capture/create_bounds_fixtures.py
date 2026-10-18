"""Add explicitly synthetic NFB1/NFB2 clipping to an owned whole-scene fixture."""
import argparse,struct,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
raw=a.input.read_bytes();sections=[]
for i in range(4):
 off,size=struct.unpack_from('<QQ',raw,64+i*16);sections.append(raw[off:off+size])
packet=sections[0];parts=[]
for i in range(5):
 off,size=struct.unpack_from('<II',packet,36+i*12);parts.append(packet[off:off+size])
world=struct.unpack_from('<I',parts[1],4)[0];entries=struct.unpack_from('<I',parts[4],4)[0];prefix=8+entries*20;assert len(parts[4])==prefix
# Dense synthetic zero indices ensure clipped cases still exercise zero/skip.
world_data=bytearray(parts[1]);at=8;pixels=[]
for i in range(world):
 c,w,h=struct.unpack_from('<III',world_data,at);pixels.append(w*h);at+=12+c*40+w*h*4
assert struct.unpack_from('<I',world_data,at)[0]==0x3149574e;at+=8
for i,pixel_count in enumerate(pixels):
 mode,size=struct.unpack_from('<II',world_data,at);at+=8;index_at=at+(pixel_count if mode==7 else 0)
 for pixel in range(pixel_count):
  value=world_data[index_at+pixel];value=0 if value%8==0 else value;world_data[index_at+pixel]=value
  if mode==7:world_data[at+pixel]=0 if value==0 else 2
 at+=size
parts[1]=bytes(world_data)
report={}
for name,count,magic in [('world-only',world,0x3142464e),('world-model',entries,0x3242464e)]:
 rects=[]
 for i in range(count):
  if i==3 or i==world:rect=(0,0,0,0)
  elif i==1:rect=(31,207,83,147)
  elif i>=world:rect=(108,135,104,132)
  else:rect=(11+i,229-i,7+i,151-i)
  rects.append(rect)
 ids=parts[4]+struct.pack('<IId',magic,count,0.0)+b''.join(struct.pack('<HHHH',*r) for r in rects)
 new=bytearray(packet[:92])
 for i,part in enumerate(parts[:-1]+[ids]):struct.pack_into('<II',new,36+i*12,len(new),len(part));new+=part
 struct.pack_into('<I',new,8,len(new));bundle=bytearray(raw[:128])
 for i,part in enumerate([bytes(new)]+sections[1:]):struct.pack_into('<QQ',bundle,64+i*16,len(bundle),len(part));bundle+=part
 struct.pack_into('<Q',bundle,16,len(bundle));dest=a.output/(name+'.nab');dest.write_bytes(bundle);report[name]={'sha256':hashlib.sha256(bundle).hexdigest(),'synthetic_bounds':rects,'world_only_models_default_full':count==world}
(a.output/'fixture-manifest.json').write_text(json.dumps(report,indent=2));print('Synthetic bounds fixtures ready')
