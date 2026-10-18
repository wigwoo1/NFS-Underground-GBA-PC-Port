from pathlib import Path
import struct,json,os
from scene_batches import batches
import export_road_preview
root=Path('work/camera');scene=list(batches(root/'world.bin'))[int(os.environ.get('NF_REPLAY_SCENE','10'))]
def h(b,o):return struct.unpack_from('<h',b,o)[0]
def u(b,o):return struct.unpack_from('<H',b,o)[0]
def i(b,o):return struct.unpack_from('<i',b,o)[0]
active={};walls=[];flags_seen=set()
for e in scene['events']:
 b=e['blocks']
 if e['pc']==0x03001800:active[b[1][0]]=b
 elif e['pc']==0x03000304:
  p=active[b[1][0]];count=u(p[4][1],2);index=(b[5][0]-p[5][0])//68
  assert 0<=index<count and p[5][0]+index*68==b[5][0]
  s=b[5][1];o=b[9][1] or bytes(32);n=(index+1)%count;ns=p[5][1][n*68:(n+1)*68];no=p[10+n][1] or bytes(32)
  x=i(s,0)+h(o,0);z=i(s,4)+h(o,2);nx=i(ns,0)+h(no,0);nz=i(ns,4)+h(no,2)
  vertices=[(x,h(s,8)+h(o,8),z),(nx,h(s,12)+h(o,8),nz),(nx,h(s,14)+h(o,10),nz),(x,h(s,10)+h(o,10),z)]
  mat=b[8][1];width=1<<u(mat,36);height=u(mat,38);flags=e['regs'][2];flags_seen.add(hex(flags))
  anim=b[70][1];assert len(anim)==8
  start=u(s,40)/width+h(anim,4)/(256*width);end=start+u(s,64)/256
  if flags&2:start,end=end,start
  if flags&128:
   v=[i(s,16),i(s,20),i(s,28),i(s,24)];v=[(value+h(anim,6)/2)/(128*height) for value in v]
  else:
   # Default rasterizer treats these as a start and span, not two endpoints.
   vertical_start=(i(s,16)+(h(anim,6)>>1))/(128*height)
   vertical_span=(i(s,24)+(h(anim,6)>>1))/(128*height)
   v=[vertical_start,vertical_start,vertical_start+vertical_span,vertical_start+vertical_span]
  uv=[(start,v[0]),(end,v[1]),(end,v[2]),(start,v[3])]
  palette=struct.unpack('<256H',b[67][1]);rgba=bytearray();assert len(b[66][1])==width*height
  for pixel in b[66][1]:
   c=palette[pixel];rgba.extend(((c&31)*255//31,((c>>5)&31)*255//31,((c>>10)&31)*255//31,255 if pixel else 0))
  walls.append((vertices,uv,width,height,rgba))
assert walls
data=bytearray((root/'road-preview.bin').read_bytes());struct.pack_into('<I',data,4,struct.unpack_from('<I',data,4)[0]+len(walls))
for vertices,uv,width,height,rgba in walls:
 data.extend(struct.pack('<3I',4,width,height))
 for vertex in vertices:data.extend(struct.pack('<3d',*vertex))
 for vertex in uv:data.extend(struct.pack('<2d',*vertex))
 data.extend(rgba)
(root/'wall-scene-preview.bin').write_bytes(data)
(root/'empty-world-preview.bin').write_bytes(struct.pack('<2I',0x31574650,0))
report={'scene_serial':scene['serial'],'captured_wall_draws':len(walls),'flags':sorted(flags_seen),
 'scope':'Default wall vertical start/span recovered; extended UV projection, shading, LOD and visibility remain incomplete. Use draw-order.bin for captured cross-surface ordering.'}
(root/'wall-preview-input.json').write_text(json.dumps(report,indent=2));print(report)
