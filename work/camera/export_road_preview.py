from pathlib import Path
import struct,json,os
from scene_batches import batches
root=Path('work/camera');scene=list(batches(root/'world.bin'))[int(os.environ.get('NF_REPLAY_SCENE','10'))]
def h(b,o):return struct.unpack_from('<h',b,o)[0]
def u(b,o):return struct.unpack_from('<H',b,o)[0]
def i(b,o):return struct.unpack_from('<i',b,o)[0]
roads=[]
for e in scene['events']:
 if e['pc']!=0x030032f0:continue
 b=e['blocks'];desc=b[4][1];src=b[5][1];mat=b[8][1];count=u(desc,2);width=1<<u(mat,36);height=u(mat,38)//2
 # Both surface branches use the same base UV ring; descriptor +8 is drawn
 # first and +4 second. This sample has only +8 surfaces.
 assert u(desc,8) and not u(desc,4),'Uncovered alternate surface'
 face=b[42][1] or bytes(20);vertices=[];uv=[]
 for n in range(count):
  o=b[10+n][1] or bytes(32);base=n*68
  vertices.append((i(src,base)+h(o,0),h(src,base+56)+h(o,6)+h(face,6),i(src,base+4)+h(o,2)))
  uv.append((i(src,base+32)/16384+h(b[9][1],4)/(256*width),i(src,base+36)/16384+h(b[9][1],6)/(512*height)))
 palette=struct.unpack('<256H',b[67][1]);rgba=bytearray();packed=b[66][1];assert len(packed)==width*height*2
 for y in range(height):
  for x in range(width):
   p=palette[packed[y*width*2+x]];rgba.extend(((p&31)*255//31,((p>>5)&31)*255//31,((p>>10)&31)*255//31,255))
 roads.append((vertices,uv,width,height,rgba))
assert roads
with (root/'road-preview.bin').open('wb') as f:
 f.write(struct.pack('<2I',0x31444652,len(roads)))
 for vertices,uv,w,hgt,rgba in roads:
  f.write(struct.pack('<3I',len(vertices),w,hgt))
  for v in vertices:f.write(struct.pack('<3d',*v))
  for v in uv:f.write(struct.pack('<2d',*v))
  f.write(rgba)
(root/'road-preview-input.json').write_text(json.dumps({'scene_serial':scene['serial'],'roads':len(roads),'scope':'Captured +8 road surfaces, packed textures decoded; visibility and alternate surface branch not complete.'},indent=2))
print('Exported',len(roads),'textured road surfaces')
