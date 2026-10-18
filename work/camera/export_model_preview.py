from pathlib import Path
import ctypes as C,json,struct,hashlib,os
from scene_batches import batches
from analyze_world import records
root=Path('work/camera')
class Point(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double)]
class Quat(C.Structure):_fields_=[('x',C.c_double),('y',C.c_double),('z',C.c_double),('w',C.c_double)]
class Pose(C.Structure):_fields_=[('position',Point),('rotation',Quat)]
d=C.CDLL(str((root/'rigid_motion.dll').resolve()));d.nf_pose_decode.argtypes=[C.POINTER(C.c_int32),C.POINTER(Point),C.POINTER(Pose)]
def pose(matrix,position):
    m=(C.c_int32*12)(*struct.unpack('<12i',matrix));p=Point(*position);out=Pose()
    assert d.nf_pose_decode(m,C.byref(p),C.byref(out));return bytes(out)
latest={};caller=None;snapshots=[];topologies=set()
for e in records(root/'world.bin'):
    b=e['blocks']
    if e['pc']==0x0806db14:latest[b[73][0]]=b[71][1]
    elif e['pc']==0x03002628:caller=e
    elif e['pc']==0x030045e0 and b[53][0] in latest:
        cb=caller['blocks'];cam=cb[63][1];position=struct.unpack_from('<3i',cb[62][1],12)
        cp=pose(cam,[-v for v in struct.unpack_from('<3i',cam,36)])
        op=pose(latest[b[53][0]],[v/256 for v in position])
        topologies.add(hashlib.sha256(b[54][1]+b[58][1]+b[59][1]+b[60][1]+b[65][1]).hexdigest())
        snapshots.append((e['frame'],cp,op,b))
assert len(topologies)==1,'Preview requires stable topology'
scene=list(batches(root/'world.bin'))[int(os.environ.get('NF_REPLAY_SCENE','10'))]
model_events=[e for e in scene['events'] if e['pc']==0x030045e0];assert len(model_events)==1
sample_index=next(index for index,s in enumerate(snapshots) if s[0]==model_events[0]['frame'])
a,b=snapshots[sample_index:sample_index+2];blocks=a[3];context=blocks[51][1]
verts=struct.unpack('<'+'h'*(len(blocks[54][1])//2),blocks[54][1]);n=len(verts)//3
indices=struct.unpack('<'+'H'*(len(blocks[58][1])//2),blocks[58][1]);assert max(indices)<n
uv_indices=struct.unpack('<'+'H'*len(indices),blocks[59][1]);uv=struct.unpack('<'+'H'*(len(blocks[65][1])//2),blocks[65][1])
width=1<<struct.unpack_from('<H',context,56)[0];height=struct.unpack_from('<H',context,58)[0]
palette=struct.unpack('<256H',blocks[67][1]);rgba=bytearray()
for index in blocks[66][1]:
    p=palette[index];rgba.extend(((p&31)*255//31,((p>>5)&31)*255//31,((p>>10)&31)*255//31,255))
assert len(rgba)==width*height*4
center=struct.unpack_from('<hh',blocks[56][1],8);scale=struct.unpack_from('<I',context,64)[0]
with (root/'model-preview.bin').open('wb') as f:
    f.write(struct.pack('<6I3d',0x314d464e,n,len(blocks[60][1]),len(indices),width,height,*center,scale))
    f.write(a[1]+b[1]+a[2]+b[2]);f.write(struct.pack('<'+'d'*len(verts),*verts))
    f.write(blocks[60][1]);f.write(blocks[58][1])
    f.write(struct.pack('<'+'d'*(len(indices)*2),*[uv[index*2+k]/32768 for index in uv_indices for k in (0,1)]))
    f.write(rgba)
report={'vertices':n,'faces':len(blocks[60][1]),'indices':len(indices),'texture_size':[width,height],
        'stable_topology_samples':len(snapshots),'source_refreshes':[a[0],b[0]],'scope':'One captured model, fixed captured texture, no scenery or gameplay.'}
(root/'model-preview-input.json').write_text(json.dumps(report,indent=2));print(report)
