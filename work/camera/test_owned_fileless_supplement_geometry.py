"""Fileless supplemental geometry parity; also runs original full-RAM invariant."""
from pathlib import Path
import struct,json
source=Path('work/camera/test_owned_fully_fileless_graph.py').read_text()
source=source.replace("'callbacks_read','associations_read'","'callbacks_read','associations_read','supplements_read'")
source=source.replace('active=False;nonempty=None;', 'supplement_records={};active=False;nonempty=None;')
source=source.replace("   cb=read('callbacks_read')", "   supplement=read('supplements_read');at=0\n   while at<len(supplement):\n    h=struct.unpack_from('<8I',supplement,at);record=supplement[at:at+32+h[5]];at+=32+h[5]\n    assert h[0]==0x3147534e and h[6] and len(record)==32+h[5]\n    supplement_records[(h[1],h[3],record[192:208])]=record\n   cb=read('callbacks_read')")
exec(compile(source,'fileless_supplement_replay','exec'))
raw=(p/'owned-supplement-geometry.bin').read_bytes();at=0;matches=0
while at<len(raw):
 h=struct.unpack_from('<8I',raw,at);record=raw[at:at+32+h[5]];at+=32+h[5]
 key=(h[1],h[3],record[192:208]);actual=supplement_records[key]
 assert actual[:28]==record[:28] and actual[32:]==record[32:]
 matches+=1
assert matches==9
r=dict(result='PASS_FILELESS_SUPPLEMENTAL_GEOMETRY',diagnostic_records_exact=matches,fileless_unique_records=len(supplement_records),original_ram_bytes_exact=294912,scope='Live raw supplemental geometry/offset/material/animation/camera/region/palette matches diagnostic capture. Building buffer only; texture ownership and atomic closed publication pending.')
(p/'owned-fileless-supplement-geometry.json').write_text(json.dumps(r,indent=2));print(r)
