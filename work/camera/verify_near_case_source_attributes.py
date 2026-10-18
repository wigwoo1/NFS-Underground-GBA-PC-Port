"""Verify owned road UV attributes against actual original clipped draw sources."""
from pathlib import Path
import json,struct,collections
p=Path('outputs/nfsug-native-renderer/camera-research');cases=json.loads((p/'original-multimodel-near-case-capture.json').read_text())['cases'];exports={e['identity'][1]:e for e in json.loads((p/'source-order-multimodel-exports.json').read_text())['exports']};rows=[]
for case in cases:
 original=case['original'];kind=case['case']['kind'];serial=case['identity'][1];b=Path(exports[serial]['path']).read_bytes();_,offset,size=struct.unpack_from('<3I',b,44);world=b[offset:offset+size];n=struct.unpack_from('<I',world,4)[0];pos=8
 for i in range(n):
  count,width,height=struct.unpack_from('<3I',world,pos);pos+=12+count*40+width*height*4
 assert struct.unpack_from('<2I',world,pos)==(0x3149574e,n);pos+=8
 for i in range(n):
  mode,length=struct.unpack_from('<2I',world,pos);pos+=8;payload=world[pos:pos+length];pos+=length
  if i==case['case']['index']:selected=(mode,payload)
 if kind!=1:
  rows.append(dict(identity=case['identity'],source=case['case']['source'],kind=kind,verified=False,reason='Wall coverage comparison pending'));continue
 mode,payload=selected;assert mode in (5,6);raw=payload[-288:];header=struct.unpack_from('<6I2i',raw);source=bytes.fromhex(original['source_hex']);descriptor=bytes.fromhex(original['descriptor_hex']);material=bytes.fromhex(original['material_hex']);animation=bytes.fromhex(original['animation_hex']);count=struct.unpack_from('<H',descriptor,2)[0]
 assert header[0]==count and len(source)==count*68;assert (header[1],header[2])==struct.unpack_from('<2H',material,36);assert tuple(header[6:8])==struct.unpack_from('<2h',animation,4)
 for i in range(count):assert struct.unpack_from('<2i',raw,32+i*8)==struct.unpack_from('<2i',source,i*68+32)
 start,vertices=original['prepared_start_count'];assert 3<=vertices<=64 and start+vertices<=64;prepared=bytes.fromhex(original['prepared_hex']);polygon=[list(struct.unpack_from('<6i',prepared,(start+i)*24)) for i in range(vertices)]
 rows.append(dict(identity=case['identity'],source=case['case']['source'],kind=kind,verified=True,source_vertices=count,prepared_vertices=vertices,prepared_polygon=polygon,mode=mode))
report=dict(result='SOURCE_ATTRIBUTES_VERIFIED',cases=rows,verified_roads=sum(r['verified'] for r in rows),pending_walls=sum(not r['verified'] for r in rows),scope='Owned count/dimensions/offsets/raw UV attributes equal actual original draw source for crossing roads. Original prepared clipped polygons captured; numeric clipped projection/UV comparison remains pending.')
(p/'near-case-source-attribute-verification.json').write_text(json.dumps(report,indent=2));print(report['verified_roads'],report['pending_walls'])
