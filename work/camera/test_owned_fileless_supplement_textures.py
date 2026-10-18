from pathlib import Path
import struct,json
source=Path('work/camera/test_owned_fully_fileless_graph.py').read_text()
source=source.replace("'callbacks_read','associations_read'","'callbacks_read','associations_read','supplement_textures_read'")
source=source.replace('active=False;nonempty=None;', 'texture_records={};active=False;nonempty=None;')
source=source.replace("   cb=read('callbacks_read')", "   textures=read('supplement_textures_read');cursor=0\n   while cursor<len(textures):\n    th=struct.unpack_from('<12I',textures,cursor);tr=textures[cursor:cursor+120+th[10]];cursor+=120+th[10]\n    assert th[11] and len(tr)==120+th[10]\n    texture_records[tuple(th[1:6])]=tr\n   cb=read('callbacks_read')")
exec(compile(source,'fileless_supplement_texture_replay','exec'))
raw=(p/'owned-supplement-textures.bin').read_bytes();at=0;matches=payload=0
while at<len(raw):
 h=struct.unpack_from('<12I',raw,at);record=raw[at:at+120+h[10]];at+=120+h[10]
 assert texture_records[tuple(h[1:6])]==record;matches+=1;payload+=h[10]
assert matches==36 and payload==38592
r=dict(result='PASS_FILELESS_SUPPLEMENTAL_TEXTURES',diagnostic_records_exact=matches,texture_bytes_exact=payload,fileless_unique_records=len(texture_records),original_ram_bytes_exact=294912,scope='Fileless resolved supplemental textures/base/animation/metadata exactly match diagnostic capture. Building sections only; atomic close and live GPU integration pending.')
(p/'owned-fileless-supplement-textures.json').write_text(json.dumps(r,indent=2));print(r)
