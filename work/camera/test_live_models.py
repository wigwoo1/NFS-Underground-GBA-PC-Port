from pathlib import Path
import struct,json,collections
from scene_batches import batches
root=Path('work/camera');expected=collections.defaultdict(list)
for scene in batches(root/'world.bin'):
 packet=(root/'packet-sequence'/f"scene-{scene['serial']:03}.packet").read_bytes()
 offset,size=struct.unpack_from('<2I',packet,36)
 for event in scene['events']:
  if event['pc']==0x030045e0:
   expected[(event['frame'],event['blocks'][51][0])].append(packet[offset:offset+size])
data=(root/'native-models-live.bin').read_bytes();position=count=checked=partial=total=unavailable=0
while position<len(data):
 assert position+24<=len(data)
 magic,frame,context,obj,camera,size=struct.unpack_from('<6I',data,position);position+=24
 assert magic==0x334d464e and size<=len(data)-position,(count,frame,size)
 if not size:
  assert not expected[(frame,context)] and count==0,'Missing pose within complete capture'
  count+=1;unavailable+=1;continue
 assert size>=160
 payload=data[position:position+size];position+=size;count+=1
 assert struct.unpack_from('<I',payload)[0]==0x324d464e
 key=(frame,context)
 if expected[key]:
  reference=expected[key].pop(0)
  assert payload==reference,(key,next((i for i,(a,b) in enumerate(zip(payload,reference)) if a!=b),None))
  checked+=1;total+=size
 else:partial+=1
assert checked==48 and not any(expected.values()) and count<1024
memory=json.loads((root/'native-models-live-capture-tests.json').read_text())
assert memory['capture_preserves_memory']
report={'result':'PASS','live_native_model_records':count,'complete_scene_sections_byte_identical':checked,'verified_bytes':total,'partial_scene_records_outside_comparison':partial,'initial_partial_without_prior_pose':unavailable,'capture_preserves_memory':True,'scope':'Live native mesh, texture and independent camera/object pose extraction; complete scene publication and live presentation remain unfinished.'}
(root/'live-model-tests.json').write_text(json.dumps(report,indent=2));print(report)
