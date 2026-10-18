from pathlib import Path
import struct,json
from owned_portal_traversal import traverse
p=Path('work/camera');raw=(p/'owned-traversals.bin').read_bytes();rb=(p/'road-correction-reciprocal.bin').read_bytes();reciprocal=struct.unpack('<'+str(len(rb)//4)+'I',rb);scenes={};offset=0
while offset<len(raw):
 h=struct.unpack_from('<12I',raw,offset);offset+=48
 if h[1]==1:
  n=432+h[9]*68;data=raw[offset:offset+n];offset+=n
  scene=scenes.setdefault(h[2],dict(graph={},expected=[],matrix=struct.unpack_from('<12i',data,304),framebuffer=bytes(data[352:416])))
  parent=struct.unpack_from('<8H',data,416)[:7];scene['expected'].append(parent)
  graph_entry=(bytes(data[432:]),struct.unpack_from('<H',data,92)[0],struct.unpack_from('<H',data,94)[0])
  if h[5] in scene['graph']:assert scene['graph'][h[5]]==graph_entry
  scene['graph'][h[5]]=graph_entry
 else:offset+=h[5]
checks=[]
for refresh,scene in scenes.items():
 result=traverse(scene['graph'],scene['matrix'],scene['framebuffer'],scene['expected'][0],reciprocal)
 assert result==scene['expected'],(refresh,result,scene['expected'])
 # Removing a required raw descriptor must fail explicitly, not silently hide it.
 graph=dict(scene['graph']);del graph[result[-1][0]]
 try:traverse(graph,scene['matrix'],scene['framebuffer'],result[0],reciprocal)
 except ValueError:pass
 else:raise AssertionError('Missing descriptor accepted')
 checks.append(dict(refresh=refresh,regions=len(result),max_depth=max(x[6] for x in result)))
r=dict(result='PASS_OWNED_RAW_PORTAL_QUEUE',scenes=len(checks),regions=sum(x['regions'] for x in checks),checks=checks,missing_source_rejected=True,scope='Native queue owns traversal order from raw graph and camera. Graph/root supplied captured interval; completeness outside original visibility is not established.')
(p/'owned-portal-queue-tests.json').write_text(json.dumps(r,indent=2));print(r['result'],r['scenes'],r['regions'])
