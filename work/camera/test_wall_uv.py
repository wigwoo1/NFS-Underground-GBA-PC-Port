from pathlib import Path
import json,struct
from scene_batches import records
root=Path('work/camera')
def h(b,o):return struct.unpack_from('<h',b,o)[0]
def u(b,o):return struct.unpack_from('<H',b,o)[0]
def i(b,o):return struct.unpack_from('<i',b,o)[0]
checked=0;maximum=0;skipped=0;textures=set()
for e in records(root/'world.bin'):
 if e['pc']!=0x03000304:continue
 b=e['blocks'];s=b[5][1];edge=b[6][1];mat=b[8][1];anim=b[70][1]
 width=1<<u(mat,36);height=u(mat,38);assert len(b[66][1])==width*height
 textures.add((i(mat,40),width,height))
 start=u(s,40)/width+h(anim,4)/(256*width);end=start+u(s,64)/256
 if e['regs'][2]&2:start,end=end,start
 for offset,clip_flag,expected in [(16,8,start),(20,16,end)]:
  if u(edge,48)&clip_flag:skipped+=1;continue
  actual=i(edge,offset)/(128*width);error=abs(actual-expected-round(actual-expected))
  maximum=max(maximum,error);checked+=1
  # The original takes the arithmetic half of the signed animation offset.
  assert error<=1/(256*width)+1e-12,(e['id'],offset,error)
assert checked
report={'result':'PASS','uncut_horizontal_endpoints':checked,'clipped_endpoints_skipped':skipped,
 'maximum_normalized_U_error':maximum,'distinct_material_textures':len(textures),
 'scope':'Horizontal wall UV endpoints and texture sizes only. Vertical UV modes, shading, LOD and clipping behavior remain incomplete.'}
(root/'wall-uv-tests.json').write_text(json.dumps(report,indent=2));print(report)
