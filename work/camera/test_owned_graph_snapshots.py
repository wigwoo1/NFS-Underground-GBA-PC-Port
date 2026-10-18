from pathlib import Path
import struct,json
from owned_portal_traversal import traverse
exec(compile(Path('work/camera/test_owned_portal_queue.py').read_text().split('checks=[]')[0],'queue_reference_setup','exec'))
raw=(p/'owned-graph-snapshots.bin').read_bytes();offset=0;checks=[]
while offset<len(raw):
 h=struct.unpack_from('<8I',raw,offset);assert h[0]==0x3253474e and h[6]==1
 context=raw[offset+32:offset+928];geometry=raw[offset+928:offset+928+h[4]];offsets=raw[offset+928+h[4]:offset+928+h[4]+h[5]];assert len(offsets)==h[5]
 cursor=oc=0;graph={};scene=scenes[h[1]];assert struct.unpack_from('<12i',context,256)==scene['matrix'] and context[304:368]==scene['framebuffer']
 parent=struct.unpack_from('<8H',context,368)[:7]
 for n in range(h[3]):
  index,vertices,_,_=struct.unpack_from('<4I',geometry,cursor);cursor+=64;ring=geometry[cursor:cursor+vertices*68];cursor+=vertices*68
  graph[index]=(ring,*struct.unpack_from('<2H',context,92));oc+=vertices*32
 assert cursor==h[4] and oc==h[5]
 assert traverse(graph,struct.unpack_from('<12i',context,256),context[304:368],parent,reciprocal)==scene['expected']
 checks.append(dict(refresh=h[1],descriptors=h[3],offset_bytes=h[5],exact_regions=len(scene['expected'])))
 offset+=928+h[4]+h[5]
assert len(checks)==8
r=dict(result='PASS_OWNED_GRAPH_SCENE_SNAPSHOTS',scenes=8,checks=checks,scope='Self-owned context/geometry/offset buffers; material companion and object closure/live transport integration pending.')
(p/'owned-graph-snapshots.json').write_text(json.dumps(r,indent=2));print(r['result'],len(checks))
