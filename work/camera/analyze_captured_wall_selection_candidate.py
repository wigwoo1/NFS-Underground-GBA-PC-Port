import sys,json,struct,hashlib
from pathlib import Path
from types import SimpleNamespace
from owned_continuous_wall_visibility import select_wall
reciprocal=struct.unpack("<32768I",Path("work/camera/road-correction-reciprocal.bin").read_bytes())
visibility_rows=[]
from pathlib import Path
import numpy as np
folder=Path(sys.argv[1]);m=json.loads((folder/'manifest.json').read_text());assert len(m['rows'])==48 and not m['missed'] and m['pending']==0
rows=[];total=0;max_error=0;near_crossings=0
def half(b,o):return struct.unpack_from('<h',b,o)[0]
def word(b,o):return struct.unpack_from('<i',b,o)[0]
def raw_transform(p,m):
 def axis(x,z,k):
  value=(((x+int(m[9]))&0xffffffff)*int(m[k])+((z+int(m[11]))&0xffffffff)*int(m[6+k]))&0xffffffff
  if value>=0x80000000:value-=0x100000000
  return ((value>>14)+32768)%65536-32768
 x=int(np.floor(p[0]));z=int(np.floor(p[2]));fx=p[0]-x;fz=p[2]-z;r=[0.,p[1]+int(m[10]),0.]
 for i in range(2):
  for j in range(2):
   weight=(fx if i else 1-fx)*(fz if j else 1-fz)
   if weight:
    for k in (0,2):r[k]+=weight*axis(x+i,z+j,k)
 return np.array(r)
def rigid(p,m):
 return np.array([sum((p[j]+m[9+j])*m[j*3+k] for j in range(3)) for k in range(3)])
def near_clip(points):
 output=[]
 for j,b in enumerate(points):
  a=points[j-1];ai=a[2]>=64;bi=b[2]>=64
  if ai!=bi:
   q=a+(b-a)*((64-a[2])/(b[2]-a[2]));q[2]=64;output.append(q)
  if bi:output.append(b.copy())
 return output
for row in m['rows']:
 packet=row['world_packets'];path=folder/packet['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==packet['sha256']
 with np.load(path,allow_pickle=False) as a:
  prefix=a['source_prefix'].tobytes();assert struct.unpack_from('<I',prefix)[0]==0x3346474e
  gn=struct.unpack_from('<I',prefix,8)[0];assert len(prefix)==40+gn
  assert struct.unpack_from('<Q',prefix,24)[0]==row['epoch']
  records=[];position=40
  while position<len(prefix):
   magic,kind,context,n=struct.unpack_from('<4I',prefix,position);position+=16;assert magic==0x3147534e and kind in (1,2,3) and n==12
   blocks=[]
   for _ in range(12):
    size=struct.unpack_from('<I',prefix,position)[0];position+=4;assert size<=0x100000 and position+size<=len(prefix);blocks.append(prefix[position:position+size]);position+=size
   records.append((kind,context,blocks))
  assert position==len(prefix) and a['source_bounds'].shape==(len(records),4)
  assert a['camera'].shape==(12,) and np.isfinite(a['camera']).all() and 0<=a['source_alpha'][0]<=1
  walls=[]
  for draw,provenance in enumerate(a['provenance']):
   kind,context,view,face=map(int,provenance);assert view<len(records)
   rk,rc,blocks=records[view];assert (rk,rc)==(kind,context)
   if kind!=2:continue
   assert len(blocks[0])==136 and len(blocks[1])==64 and len(blocks[2])==8 and len(blocks[4])==48 and len(blocks[9])==512
   shift,height=struct.unpack_from('<HH',blocks[4],36);width=1<<shift;assert shift<=10 and 0<height<=1024
   indices=np.frombuffer(blocks[8],np.uint8)[:width*height].reshape(height,width);palette=np.frombuffer(blocks[9],'<u2');colors=palette[indices]
   expected=np.empty((height,width,4),np.uint8)
   for channel in range(3):
    five=(colors>>(channel*5))&31;expected[:,:,channel]=(five<<3)|(five>>2)
   expected[:,:,3]=np.where(indices==0,0,255)
   tid=int(a['texture_ids'][draw]);w,h,offset,size=map(int,a['texture_records'][tid-1]);assert (w,h)==(width,height)
   assert np.array_equal(expected.reshape(-1),a['texture_rgba'][offset:offset+size])
   bounds=a['source_bounds'][view];assert np.isfinite(bounds).all()
   expected_scissor=np.array([300+np.ceil(bounds[0]*13.5),2160-np.ceil((160-bounds[2])*13.5),300+np.ceil((bounds[1]+1)*13.5),2160-np.ceil((160-(bounds[3]+1))*13.5)],dtype=np.int32)
   actual=np.frombuffer(a['states'][draw,32:48].tobytes(),'<i4');assert np.array_equal(expected_scissor,actual),(draw,bounds,actual,expected_scissor)
   source,off,anim=blocks[0],blocks[1],blocks[2]
   x=word(source,0)+half(off,0);z=word(source,4)+half(off,2);nx=word(source,68)+half(off,32);nz=word(source,72)+half(off,34)
   world=np.array([[x,half(source,8)+half(off,8),z],[nx,half(source,12)+half(off,8),nz],[nx,half(source,14)+half(off,10),nz],[x,half(source,10)+half(off,10),z]],dtype=np.float64)
   alpha=float(a['source_alpha'][0]);camera=[]
   for point in world:
    ra=raw_transform(point,a['raw_camera_a']);rb=raw_transform(point,a['raw_camera_b']);fa=rigid(point,a['rigid_camera_a']);fb=rigid(point,a['rigid_camera_b'])
    camera.append(rigid(point,a['camera'])+(1-alpha)*(ra-fa)+alpha*(rb-fb))
   edge=(camera[0][0],camera[1][0],camera[0][2],camera[1][2],camera[0][1],camera[1][1],camera[3][1],camera[2][1])
   wall=SimpleNamespace(vertices=source[:68],offsets=off[:32])
   selection=select_wall(wall,blocks[7],edge,blocks[6],a['source_bounds'][view],blocks[11][:256],reciprocal)
   visibility_rows.append(dict(index=row['index'],draw=draw,view_index=view,visible=selection.visible,reason=selection.reason,edge=list(edge),flags=selection.flags))
   au=half(anim,4);av=half(anim,6);flags=struct.unpack_from('<I',blocks[11],256)[0]
   left=struct.unpack_from('<H',source,40)[0]/width+au/(256*width);right=left+struct.unpack_from('<H',source,64)[0]/256
   if flags&2:left,right=right,left
   top=(word(source,16)+(av>>1))/(128*height);bottom=top+(word(source,24)+(av>>1))/(128*height)
   input_points=np.column_stack((camera,[[left,top],[right,top],[right,bottom],[left,bottom]]));near_crossings+=int(any(p[2]<64 for p in input_points))
   polygon=near_clip(input_points);assert len(polygon)>=3
   expected_vertices=[]
   for j in range(1,len(polygon)-1):
    for point in (polygon[0],polygon[j],polygon[j+1]):
     reciprocal=1/point[2];expected_vertices.append([120+128*point[0]*reciprocal,87+128*point[1]*reciprocal,point[3]*reciprocal,point[4]*reciprocal,0,reciprocal,1,1,1,1])
   expected_vertices=np.asarray(expected_vertices,dtype=np.float32);actual_vertices=a['vertices'][a['offsets'][draw]:a['offsets'][draw+1]]
   assert actual_vertices.shape==expected_vertices.shape
   error=float(np.max(np.abs(actual_vertices.astype(np.float64)-expected_vertices.astype(np.float64))));max_error=max(max_error,error)
   assert np.array_equal(actual_vertices,expected_vertices),(draw,error)
   walls.append(dict(draw=draw,view_index=view,source_sha256=hashlib.sha256(blocks[0]).hexdigest(),width=width,height=height,clip=bounds.tolist(),scissor=actual.tolist()))
  total+=len(walls);rows.append(dict(index=row['index'],walls=walls))
out=dict(result='INCOMPLETE_VISIBILITY_INPUT_AUTHORITY',visibility_rows=visibility_rows,rejected_draws=sum(not r['visible'] for r in visibility_rows),frames=len(rows),wall_draws=total,near_crossing_draws=near_crossings,max_float32_vertex_error=max_error,rows=rows,scope='Exploratory replay used block11 as base material without authoritative encoding linkage. Zero placeholders cause inactive results; rejected_draws must NOT be treated as actual selection errors. Requires upstream original base material and portal call inputs. Geometry comparisons remain separate valid evidence.')
(folder/'wall-selection-audit.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ('rows','visibility_rows')})
