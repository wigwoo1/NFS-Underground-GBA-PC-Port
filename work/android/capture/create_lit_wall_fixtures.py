"""Create explicit synthetic mode3/8 lighting on captured wall geometry."""
import argparse,hashlib,json,struct
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
raw=a.input.read_bytes();sections=[]
for i in range(4):
 off,size=struct.unpack_from('<QQ',raw,64+i*16);sections.append(raw[off:off+size])
packet=sections[0];parts=[]
for i in range(5):
 off,size=struct.unpack_from('<II',packet,36+i*12);parts.append(packet[off:off+size])
world=parts[1];count=struct.unpack_from('<I',world,4)[0];at=8;sizes=[]
for i in range(count):
 c,w,h=struct.unpack_from('<III',world,at);sizes.append((w,h));at+=12+c*40+w*h*4
base=world[:at];assert struct.unpack_from('<II',world,at)==(0x3149574e,count);at+=8;old=[]
for i in range(count):
 mode,size=struct.unpack_from('<II',world,at);at+=8;old.append((mode,world[at:at+size]));at+=size
assert at==len(world);reciprocal=parts[3][-131072:];report={}
for case,new_mode in [('rgba-lit',3),('indexed-lit',8)]:
 metadata=bytearray(struct.pack('<II',0x3149574e,count));lighting=bytearray(struct.pack('<II',0x314c464e,count));lit=0
 for i,(w,h) in enumerate(sizes):
  kind=struct.unpack_from('<I',parts[4],8+i*20)[0];mode,payload=old[i];pixels=w*h
  if kind!=2:
   metadata+=struct.pack('<II',mode,len(payload))+payload;lighting+=struct.pack('<I',0);continue
  assert mode==7;lit+=1;indices=bytes(0 if v%8==0 else v for v in payload[pixels:]);states=bytes(0 if v==0 else 2 for v in indices);all_states=bytearray(states);all_indices=bytearray(indices);variants=bytearray()
  for level in range(16):
   for value in indices:
    mapped=0 if value==0 or (value+level)%5==0 else (value+level*13)%255+1
    state=0 if value==0 else 1 if mapped==0 else 2;all_states.append(state);all_indices.append(mapped)
    color=((value*3+level*7)%256,(value*5+level*11)%256,(value*7+level*13)%256) if state==2 else (255,0,255) if state==1 else (255,0,0)
    variants+=bytes((*color,0 if value==0 else 255))
  payload=bytes(all_states)+(bytes(all_indices) if new_mode==8 else b'');metadata+=struct.pack('<II',new_mode,len(payload))+payload
  start,end=[(0,15),(15,0),(7,7)][i%3];lighting+=struct.pack('<IIIII',1,start,end,w,h)+variants
 new_parts=parts.copy();new_parts[1]=base+metadata;new_parts[3]=lighting+reciprocal;new=bytearray(packet[:92])
 for i,part in enumerate(new_parts):struct.pack_into('<II',new,36+i*12,len(new),len(part));new+=part
 struct.pack_into('<I',new,8,len(new));(a.output/(case+'.nsp')).write_bytes(new);bundle=bytearray(raw[:128])
 for i,section in enumerate([bytes(new)]+sections[1:]):struct.pack_into('<QQ',bundle,64+i*16,len(bundle),len(section));bundle+=section
 struct.pack_into('<Q',bundle,16,len(bundle));(a.output/(case+'.nab')).write_bytes(bundle);report[case]={'sha256':hashlib.sha256(bundle).hexdigest(),'synthetic_lit_walls':lit,'mode':new_mode,'states':'skip0/write-zero1/opaque2','geometry':'captured, unchanged'}
# Combined lit/clip case, preserving identical index/state/light payloads.
entries=struct.unpack_from('<I',parts[4],4)[0];rects=[]
for i in range(entries):
 rect=(0,0,0,0) if i==3 else (108,135,104,132) if i>=count else (30+i,210-i,20+i,145-i);rects.append(rect)
clip_ids=parts[4]+struct.pack('<IId',0x3242464e,entries,0.0)+b''.join(struct.pack('<HHHH',*r) for r in rects)
clipped_parts=new_parts.copy();clipped_parts[4]=clip_ids;new=bytearray(packet[:92])
for i,part in enumerate(clipped_parts):struct.pack_into('<II',new,36+i*12,len(new),len(part));new+=part
struct.pack_into('<I',new,8,len(new));bundle=bytearray(raw[:128])
for i,section in enumerate([bytes(new)]+sections[1:]):struct.pack_into('<QQ',bundle,64+i*16,len(bundle),len(section));bundle+=section
struct.pack_into('<Q',bundle,16,len(bundle));(a.output/'indexed-lit-bounds.nab').write_bytes(bundle);report['indexed-lit-bounds']={'sha256':hashlib.sha256(bundle).hexdigest(),'synthetic_lit_walls':lit,'mode':8,'synthetic_bounds':rects}
(a.output/'fixture-manifest.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
