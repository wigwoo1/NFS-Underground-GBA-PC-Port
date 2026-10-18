from pathlib import Path
import struct,json,collections
from scene_batches import batches
root=Path('work/camera');expected=collections.defaultdict(list)
for scene in batches(root/'world.bin'):
 packet=(root/'packet-sequence'/f"scene-{scene['serial']:03}.packet").read_bytes();offset,length=struct.unpack_from('<2I',packet,48);world=packet[offset:offset+length];position=8
 for e in scene['events']:
  if e['pc']!=0x030032f0:continue
  n,w,h=struct.unpack_from('<3I',world,position);size=12+n*40+w*h*4
  expected[(e['frame'],e['blocks'][4][0])].append(world[position:position+size]);position+=size
data=(root/'native-roads-live.bin').read_bytes();position=0;records=0;checked=0;partial=0
while position<len(data):
 assert position+16<=len(data);magic,frame,descriptor,size=struct.unpack_from('<4I',data,position);position+=16
 assert magic==0x3152464e and size>0 and size<=len(data)-position
 payload=data[position:position+size];position+=size;records+=1
 key=(frame,descriptor)
 if expected[key]:assert payload==expected[key].pop(0),key;checked+=1
 else:partial+=1
assert not any(expected.values()) and checked==199 and records<4096
report={'result':'PASS','live_native_road_records':records,'complete_scene_records_byte_identical':checked,'partial_scene_records_outside_comparison':partial,'scope':'Native live road extraction only; wall/model extraction and complete packet publication remain unfinished.'}
(root/'live-road-tests.json').write_text(json.dumps(report,indent=2));print(report)
