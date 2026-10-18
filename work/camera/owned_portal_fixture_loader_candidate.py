"""Pair original traversal fixtures with complete raw graphs by exact refresh."""
import struct
from pathlib import Path
def load(folder):
 folder=Path(folder);raw=(folder/'owned-traversals.bin').read_bytes();scenes={};at=0
 while at<len(raw):
  assert at+48<=len(raw);h=struct.unpack_from('<12I',raw,at);at+=48
  if h[1]!=1:assert at+h[5]<=len(raw);at+=h[5];continue
  size=432+h[9]*68;assert at+size<=len(raw);data=raw[at:at+size];at+=size
  matrix=struct.unpack_from('<12i',data,304);framebuffer=data[352:416]
  scene=scenes.setdefault(h[2],dict(graph={},expected=[],matrix=matrix,framebuffer=framebuffer))
  assert scene['matrix']==matrix and scene['framebuffer']==framebuffer
  scene['expected'].append(struct.unpack_from('<8H',data,416)[:7])
  entry=(data[432:],*struct.unpack_from('<2H',data,92))
  assert h[5] not in scene['graph'] or scene['graph'][h[5]]==entry
  scene['graph'][h[5]]=entry
 raw=(folder/'owned-portal-graphs.bin').read_bytes();at=0;graphs={};unpaired=[]
 while at<len(raw):
  assert at+32<=len(raw);h=struct.unpack_from('<8I',raw,at);at+=32;assert h[6]==1 and at+h[5]<=len(raw)
  data=raw[at:at+h[5]];at+=h[5];cursor=0;rings={}
  for _ in range(h[4]):
   assert cursor+64<=len(data);index,n,*_=struct.unpack_from('<4I',data,cursor);cursor+=64
   assert index not in rings and 0<n<=32 and cursor+n*68<=len(data)
   rings[index]=data[cursor:cursor+n*68];cursor+=n*68
  assert cursor==len(data)
  if h[1] not in scenes:unpaired.append(h[1]);continue
  scene=scenes[h[1]];bounds={v[1:] for v in scene['graph'].values()};assert len(bounds)==1
  top,bottom=next(iter(bounds));graph={key:(ring,top,bottom) for key,ring in rings.items()}
  for key,value in scene['graph'].items():assert graph[key]==value
  assert h[1] not in graphs;graphs[h[1]]=graph
 assert set(scenes)<=set(graphs),('Original traversal graph missing',set(scenes)-set(graphs))
 table=struct.unpack('<32768I',(folder/'road-correction-reciprocal.bin').read_bytes())
 return scenes,graphs,table,unpaired
