from pathlib import Path
import struct,json,collections
from scene_batches import batches
root=Path('work/camera');expected=collections.defaultdict(list)
for scene in batches(root/'world.bin'):
 packet=(root/'packet-sequence'/f"scene-{scene['serial']:03}.packet").read_bytes();wo,ws=struct.unpack_from('<2I',packet,48);lo,ls=struct.unpack_from('<2I',packet,72);world=packet[wo:wo+ws];lighting=packet[lo:lo+ls];wp=lp=8
 for _ in range(sum(e['pc']==0x030032f0 for e in scene['events'])):n,w,h=struct.unpack_from('<3I',world,wp);wp+=12+n*40+w*h*4;lp+=4
 for e in scene['events']:
  if e['pc']!=0x03000304:continue
  n,w,h=struct.unpack_from('<3I',world,wp);size=12+n*40+w*h*4;lit=struct.unpack_from('<I',lighting,lp)[0];light_size=20+w*h*64 if lit else 4
  expected[(e['frame'],e['blocks'][5][0])].append((world[wp:wp+size],lighting[lp:lp+light_size]));wp+=size;lp+=light_size
data=(root/'native-walls-live.bin').read_bytes();position=0;count=checked=partial=0
while position<len(data):
 assert position+24<=len(data);magic,frame,descriptor,source,size,light_size=struct.unpack_from('<6I',data,position);position+=24
 assert magic==0x3257464e and size>0 and light_size>0 and size+light_size<=len(data)-position
 payload=(data[position:position+size],data[position+size:position+size+light_size]);position+=size+light_size;count+=1
 key=(frame,source)
 if expected[key]:assert payload==expected[key].pop(0),key;checked+=1
 else:partial+=1
assert checked==728 and not any(expected.values()) and count<4096
report={'result':'PASS','live_native_wall_records':count,'complete_scene_records_byte_identical':checked,'partial_scene_records_outside_comparison':partial,'scope':'Live wall/lighting extraction only; model/pose extraction and complete scene publication remain unfinished.'}
(root/'live-wall-tests.json').write_text(json.dumps(report,indent=2));print(report)
