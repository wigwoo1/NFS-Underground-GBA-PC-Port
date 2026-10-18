from pathlib import Path
import struct,json,hashlib
root=Path('work/camera');data=(root/'native-scenes-live.bin').read_bytes();position=0;count=0
while position<len(data):
 assert len(data)-position>=96
 magic,version,size,sections,serial,begin,end,page=struct.unpack_from('<8I',data,position)
 assert magic==0x3150534e and version==1 and sections==5 and 96<=size<=len(data)-position
 assert serial==count and end>begin and page<=1
 packet=data[position:position+size]
 reference=(root/'packet-sequence'/f'scene-{serial:03}.packet').read_bytes()
 assert packet==reference,serial
 position+=size;count+=1
assert count==48
capture=json.loads((root/'native-scenes-live-capture-tests.json').read_text())
assert capture['capture_preserves_memory']
assert capture['scene_stats']=={'closed_scenes':48,'published':48,'rejected':0,'write_failures':0}
report={'result':'PASS','live_complete_packets_byte_identical':count,'verified_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'capture_preserves_memory':True,'scene_stats':capture['scene_stats'],'scope':'Live native extraction and complete-scene serialization from original game hooks. Diagnostic file sink only; renderer handoff, transition epochs and live pacing remain pending.'}
(root/'live-scene-tests.json').write_text(json.dumps(report,indent=2));print(report)
