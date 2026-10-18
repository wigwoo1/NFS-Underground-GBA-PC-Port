from pathlib import Path
import struct,json
from owned_portal_traversal import traverse
exec(compile(Path('work/camera/test_owned_portal_queue.py').read_text().split('checks=[]')[0],'queue_reference_setup','exec'))
raw=(p/'owned-portal-graphs.bin').read_bytes();offset=0;checks=[]
while offset<len(raw):
 magic,refresh,state,root,count,n,ok,_=struct.unpack_from('<8I',raw,offset);offset+=32;assert magic==0x3147504e and ok==1
 payload=raw[offset:offset+n];offset+=n;cursor=0;graph={};links=set();scene=scenes[refresh]
 top,bottom=next(iter(scene['graph'].values()))[1:]
 for i in range(count):
  index,vertices,desc,points=struct.unpack_from('<4I',payload,cursor);cursor+=16;descriptor=payload[cursor:cursor+48];cursor+=48;ring=bytes(payload[cursor:cursor+vertices*68]);cursor+=vertices*68
  assert index not in graph and vertices==struct.unpack_from('<H',descriptor,2)[0]
  graph[index]=(ring,top,bottom)
  links.update(struct.unpack_from('<H',ring,j*68+48)[0] for j in range(vertices))
 assert cursor==n and links-{65535}<=graph.keys()
 for index,v in scene['graph'].items():assert graph[index]==v
 result=traverse(graph,scene['matrix'],scene['framebuffer'],scene['expected'][0],reciprocal)
 assert result==scene['expected']
 checks.append(dict(refresh=refresh,reachable_descriptors=count,original_visited=len(scene['graph']),exact_regions=len(result),bytes=n))
assert len(checks)==8
r=dict(result='PASS_COMPLETE_REACHABLE_PORTAL_GRAPH',scenes=len(checks),checks=checks,scope='Complete directed portal-link closure from supplied root; render-material ownership and root selection still pending.')
(p/'owned-complete-graph-tests.json').write_text(json.dumps(r,indent=2));print(r['result'],[(x['reachable_descriptors'],x['original_visited']) for x in checks])
