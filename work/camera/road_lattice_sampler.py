"""Diagnostic source-corner texture sampling; no live renderer adoption."""
from pathlib import Path
import ctypes as C,math,struct
p=Path(__file__).resolve().parent
dll=C.CDLL(str(p/'road-row-lattice-coverage.dll'));contributors=dll.nf_road_row_lattice_contributors;contributors.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p]
span=C.CDLL(str(p/'road-span-padding-segmented.dll')).nf_road_span_transition_at;span.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_void_p,C.c_void_p]
uv=C.CDLL(str(p/'road-pair-uv-continuous.dll')).nf_road_pair_uv_continuous;uv.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_double,C.c_void_p,C.c_void_p]
def sample_contributors(ring,bounds,texture,normalization,table,destination):
 data=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r));items=(C.c_double*(4096*4))();count=C.c_uint();assert contributors(data,len(ring),(C.c_uint16*4)(*bounds),table,destination,items,4096,C.byref(count))
 width,height=struct.unpack_from('<2I',texture);plane=texture[8:];assert len(plane)==width*height;active=[i for i,r in enumerate(ring) if r[1]!=math.floor(r[1])];result=[]
 for i in range(count.value):
  mask,row,x,weight=items[i*4:i*4+4];corner=[r.copy() for r in ring]
  for k,vertex in enumerate(active):corner[vertex][1]=math.floor(ring[vertex][1])+((int(mask)>>k)&1)
  geometry=(C.c_double*(len(corner)*6))(*(v for r in corner for v in r));edges=(C.c_double*8)();assert span(geometry,len(corner),row,table,edges),'Covered contributor span unresolved'
  start=2*math.floor(edges[0]/2);pairs=math.floor((edges[4]-edges[0])/2)+2;pair=(x-start)//2;assert 0<=pair<pairs;sample=(C.c_double*2)();assert uv((C.c_double*3)(*edges[1:4]),(C.c_double*3)(*edges[5:8]),pairs,pair,table,sample)
  tx=(2*math.floor(sample[0]/(65536*normalization[0])*(width/2))+int(x)%2)%width;ty=math.floor(sample[1]/(65536*normalization[1])*height)%height
  result.append(dict(mask=int(mask),source_row=row,source_x=x,weight=weight,uv=list(sample),index=plane[ty*width+tx]))
 return result

def compose_palette(contributors,palette):
 """Premultiplied RGB in 0..255 units plus coverage, no index averaging.
 BGR555 bit replication matches captured original-game display colors. Index zero is a
 real road color; source coverage controls alpha, not the texture index.
 """
 assert len(palette)==512
 rgb=[0.,0.,0.];coverage=0.
 for contributor in contributors:
  weight=contributor['weight'];index=contributor['index'];assert 0<=weight<=1 and 0<=index<=255
  color=struct.unpack_from('<H',palette,index*2)[0]
  for channel in range(3):
   component=(color>>(channel*5))&31;rgb[channel]+=weight*((component<<3)|(component>>2))
  coverage+=weight
 assert coverage<=1+1e-10
 return (*rgb,coverage)

def sample_contributor_buffer(ring,bounds,texture,normalization,table):
 """Evaluate every destination with one ledger per source corner.
 Diagnostic CPU oracle: keeps each corner's texture sample separate.
 """
 ledger=C.CDLL(str(p/'road-write-ledger.dll')).nf_road_write_ledger
 ledger.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p]
 width,height=struct.unpack_from('<2I',texture);plane=texture[8:];assert len(plane)==width*height
 active=[i for i,r in enumerate(ring) if r[1]!=math.floor(r[1])];assert len(active)<=12
 result=[[] for _ in range(38400)]
 for mask in range(1<<len(active)):
  corner=[r.copy() for r in ring];weight=1.
  for k,i in enumerate(active):
   bit=(mask>>k)&1;t=ring[i][1]-math.floor(ring[i][1]);weight*=t if bit else 1-t;corner[i][1]=math.floor(ring[i][1])+bit
  if not weight:continue
  geometry=(C.c_double*(len(corner)*6))(*(v for r in corner for v in r));writes=(C.c_int16*(38400*2))();assert ledger(geometry,len(corner),(C.c_uint16*4)(*bounds),table,writes)
  rows={};samples={}
  for destination in range(38400):
   row,x=writes[destination*2:destination*2+2]
   if row<0:continue
   if row not in rows:
    edges=(C.c_double*8)();assert span(geometry,len(corner),row,table,edges);rows[row]=list(edges)
   edges=rows[row];pairs=math.floor((edges[4]-edges[0])/2)+2;pair=(x-2*math.floor(edges[0]/2))//2;assert 0<=pair<pairs
   key=(row,pair)
   if key not in samples:
    sample=(C.c_double*2)();assert uv((C.c_double*3)(*edges[1:4]),(C.c_double*3)(*edges[5:8]),pairs,pair,table,sample);samples[key]=list(sample)
   sample=samples[key];tx=(2*math.floor(sample[0]/(65536*normalization[0])*(width/2))+x%2)%width;ty=math.floor(sample[1]/(65536*normalization[1])*height)%height
   result[destination].append(dict(mask=mask,source_row=row,source_x=x,weight=weight,uv=sample,index=plane[ty*width+tx]))
 return result
