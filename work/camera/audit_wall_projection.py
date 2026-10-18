"""Diagnostic comparison only; never used for motion matching or rendering."""
from pathlib import Path
import struct,json
from scene_batches import batches
root=Path('work/camera');p=(root/'reference-scene-0.packet').read_bytes()
sections={t:p[o:o+n] for t,o,n in (struct.unpack_from('<3I',p,32+i*12) for i in range(5))}
m=sections[1];proj=struct.unpack_from('<3d',m,24);pose=struct.unpack_from('<7d',m,48);pos=pose[:3];qx,qy,qz,qw=pose[3:]
def rotate(v):
 x,y,z=[v[i]-pos[i] for i in range(3)]
 tx,ty,tz=2*(qy*z-qz*y),2*(qz*x-qx*z),2*(qx*y-qy*x)
 return x+qw*tx+qy*tz-qz*ty,y+qw*ty+qz*tx-qx*tz,z+qw*tz+qx*ty-qy*tx
w=sections[2];off=8;ids=sections[5]
events={e['blocks'][5][0]:e for e in next(batches(root/'shading.bin'))['events'] if e['pc']==0x03000304}
rows=[]
for i in range(struct.unpack_from('<I',w,4)[0]):
 n,tw,th=struct.unpack_from('<3I',w,off)
 verts=[rotate(struct.unpack_from('<3d',w,off+12+j*24)) for j in range(n)]
 identity=struct.unpack_from('<5I',ids,8+i*20);off+=12+n*40+tw*th*4
 if identity[0]!=2:continue
 e=events[identity[2]];edge=struct.unpack_from('<8h',e['blocks'][6][1])
 xy=[(proj[0]+proj[2]*x/z,proj[1]+proj[2]*y/z) for x,y,z in verts]
 width=((edge[1]+1)>>1)-(edge[0]>>1)
 rows.append(dict(source=hex(identity[2]),event=e['id'],flags=hex(e['regs'][2]),original_edge=list(edge),
                  original_column_width=width,original_early_width_reject=width<=1,native_vertices=xy))
assert len(rows)==len(events)==22
report=dict(scene=0,walls=rows,width_rejected=sum(r['original_early_width_reject'] for r in rows),
 scope='World-projected native vertices compared to original prepared edges. Evidence for investigating visibility/materials; not a rendering rule or motion matcher.')
(root/'wall-projection-audit.json').write_text(json.dumps(report,indent=2))
print('scene=0 walls=',len(rows),'original_width_rejects=',report['width_rejected'])
