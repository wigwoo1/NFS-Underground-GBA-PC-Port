"""Bundle one retained scene; no future camera/object pose is included."""
from pathlib import Path
import struct,json,os,hashlib
from scene_batches import batches
from surface_identity import wall_identity
root=Path('work/camera');serial=int(os.environ.get('NF_REPLAY_SCENE','10'));scene=list(batches(root/'world.bin'))[serial]
for filename,key in [('wall-preview-input.json','scene_serial'),('wall-lighting-input.json','scene'),('draw-order.json','scene_serial')]:
 assert json.loads((root/filename).read_text())[key]==serial,'Re-export all components for the same scene'
model_event=next(e for e in scene['events'] if e['pc']==0x030045e0)
assert json.loads((root/'model-preview-input.json').read_text())['source_refreshes'][0]==model_event['frame']
model=(root/'model-preview.bin').read_bytes()
current=bytearray(model[:48]+model[48:104]+model[160:216]+model[272:]);struct.pack_into('<I',current,0,0x324d464e)
roads=[e for e in scene['events'] if e['pc']==0x030032f0];walls=[e for e in scene['events'] if e['pc']==0x03000304]
caller=next(e for e in scene['events'] if e['pc']==0x03002628)
identity=bytearray(struct.pack('<2I',0x3149464e,len(roads)+len(walls)+1))
for e in roads:identity.extend(struct.pack('<5I',1,e['blocks'][1][0],e['blocks'][4][0],8,0))
for e in walls:identity.extend(struct.pack('<5I',2,*wall_identity(e)[1:],0))
identity.extend(struct.pack('<5I',3,caller['blocks'][61][0],caller['blocks'][62][0],model_event['blocks'][52][0],0))
sections=[current,(root/'wall-scene-preview.bin').read_bytes(),(root/'draw-order.bin').read_bytes(),(root/'wall-lighting.bin').read_bytes(),identity]
packet=bytearray(96)
for index,section in enumerate(sections):
 while len(packet)%8:packet.append(0)
 offset=len(packet);packet.extend(section);struct.pack_into('<3I',packet,32+index*12,index+1,offset,len(section))
struct.pack_into('<8I',packet,0,0x3150534e,1,len(packet),5,serial,scene['begin_refresh'],scene['end_refresh'],scene['display_page'])
(root/'scene-packet.bin').write_bytes(packet)
report={'scene':serial,'bytes':len(packet),'sha256':hashlib.sha256(packet).hexdigest(),'sections':['current model and poses','world surfaces','draw order','lighting','stable identities'],'scope':'One captured model and current supported world surfaces; no future pose, HUD, sky, full LOD or live extraction.'}
(root/'scene-packet-input.json').write_text(json.dumps(report,indent=2));print(report)
