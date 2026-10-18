from pathlib import Path
import struct,json
from analyze_world import records
from scene_batches import batches
from export_model_preview import snapshots
root=Path('work/camera');target=snapshots[10][0]
scene=next(s for s in batches(root/'world.bin') if any(e['pc']==0x030045e0 and e['frame']==target for e in s['events']))
events=scene['events']
def s16(b,o):return struct.unpack_from('<h',b,o)[0]
def u16(b,o):return struct.unpack_from('<H',b,o)[0]
def s32(b,o):return struct.unpack_from('<i',b,o)[0]
polys=[];seen=set()
for e in events:
    if e['pc']!=0x03001800:continue
    b=e['blocks'];descriptor=b[4][1];identity=b[4][0]
    if identity in seen:continue
    seen.add(identity);src=b[5][1];count=u16(descriptor,2);points=[];offsets=[]
    for i in range(count):
        s=src[i*68:(i+1)*68];o=b[10+i][1] or bytes(32);offsets.append(o)
        points.append((s32(s,0)+s16(o,0),s32(s,4)+s16(o,2)))
    face_offset=b[42][1] or bytes(20)
    for material,height_offset,adjust in [(8,56,6),(4,58,4)]:
        if not u16(descriptor,material):continue
        vertices=[(points[i][0],s16(src,i*68+height_offset)+s16(offsets[i],adjust)+s16(face_offset,adjust),points[i][1]) for i in range(count)]
        polys.append((1,vertices))
    for i in range(count):
        s=src[i*68:(i+1)*68];o=offsets[i]
        if not u16(s,44):continue
        x,z=points[i];nx,nz=points[(i+1)%count]
        polys.append((2,[(x,s16(s,8)+s16(o,8),z),(nx,s16(s,12)+s16(o,8),nz),
                         (nx,s16(s,14)+s16(o,10),nz),(x,s16(s,10)+s16(o,10),z)]))
assert polys
with (root/'world-preview.bin').open('wb') as f:
    f.write(struct.pack('<2I',0x31574650,len(polys)))
    for kind,vertices in polys:
        f.write(struct.pack('<2I',kind,len(vertices)))
        for v in vertices:f.write(struct.pack('<3d',*v))
report={'refresh':target,'source_faces':len(seen),'road_rings':sum(k==1 for k,v in polys),'wall_quads':sum(k==2 for k,v in polys),
        'scene_serial':scene['serial'],'display_refresh':scene['end_refresh'],'display_page':scene['display_page'],
        'scope':'World-coordinate wireframe diagnostic. Includes captured candidate edges; material visibility and textures are not reproduced.'}
(root/'world-preview-input.json').write_text(json.dumps(report,indent=2));print(report)
