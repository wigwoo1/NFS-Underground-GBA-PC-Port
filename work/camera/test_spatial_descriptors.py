import ctypes as C,struct,random,json
from pathlib import Path
from owned_graph_packet import GraphPacket
from owned_spatial_descriptors import SpatialDescriptors
from owned_root_offset_queries import fixed_queries
folder=Path('work/camera/prototype-runs/fullscene-failure-1791274790496290000');graphs=[GraphPacket.decode((folder/(x+'.graph.bin')).read_bytes()) for x in ('older','newer')];d=C.CDLL(str(Path('work/camera/visibility-probe-wide.dll').resolve()));Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint,C.c_void_p,C.c_size_t);d.nfs_visibility_select.argtypes=[C.c_void_p,Read,C.c_void_p,C.c_void_p];d.nfs_visibility_fallback.argtypes=[C.c_void_p,Read,C.c_void_p,C.c_void_p];rng=random.Random(24);checks=0
for graph in graphs:
 spatial=SpatialDescriptors(graph);memory={};at=offset=0;state=bytearray(graph.context[:256]);offsetbase=struct.unpack_from('<I',state,24)[0]
 def add(addr,data):
  for i,v in enumerate(data):
   if addr+i in memory:assert memory[addr+i]==v
   memory[addr+i]=v
 while at<len(graph.geometry):
  key,n,descaddr,pointaddr=struct.unpack_from('<4I',graph.geometry,at);add(descaddr,graph.geometry[at+16:at+64]);at+=64;ring=graph.geometry[at:at+n*68];at+=n*68;add(pointaddr,ring)
  for i in range(n):
   index=struct.unpack_from('<H',ring,i*68+42)[0]
   if index!=65535:add(offsetbase+index*32,graph.offsets[offset+i*32:offset+(i+1)*32])
  offset+=n*32
 @Read
 def read(ctx,address,out,size):
  if not all(address+i in memory for i in range(size)):return 0
  C.memmove(out,bytes(memory[address+i] for i in range(size)),size);return 1
 current=struct.unpack_from('<H',state,234)[0];m=struct.unpack_from('<12i',graph.context,256)
 for i in range(100):
  point=(-m[9]+rng.randrange(-120,121),-m[11]+rng.randrange(-120,121));struct.pack_into('<II',state,192,point[0]&0xffffffff,0);struct.pack_into('<I',state,200,point[1]&0xffffffff);out=C.c_uint();assert d.nfs_visibility_select(bytes(state),read,None,C.byref(out));assert spatial.select(current,point)==out.value;assert d.nfs_visibility_fallback(bytes(state),read,None,C.byref(out));assert spatial.fallback(current,point)==out.value;checks+=1
 root,pair=spatial.pair_root(current,fixed_queries(m));assert root==struct.unpack_from('<H',graph.context,368)[0]
print('PASS',checks,'ordered native spatial selections; both captured paired-query roots exact')

