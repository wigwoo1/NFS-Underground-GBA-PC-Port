from pathlib import Path
import struct,json
from owned_supplemental_region import region
p=Path('work/camera');raw=(p/'owned-supplements.bin').read_bytes();assert len(raw)%460==0;checks=[]
for o in range(0,len(raw),460):
 h=struct.unpack_from('<6I',raw,o);assert h[0]==0x3150534e
 source=bytes(raw[o+24:o+188]);bounds=struct.unpack_from('<4H',raw,o+204+226);expected=struct.unpack_from('<8H',raw,o+188);assert region(source,bounds)==expected
 base=struct.unpack_from('<I',raw,o+204+60)[0];assert (h[3]-base)%164==0
 disabled=bytearray(source);struct.pack_into('<H',disabled,10,struct.unpack_from('<H',source,10)[0]&~16);assert region(disabled,bounds) is None
 checks.append(dict(refresh=h[1],object_index=(h[3]-base)//164,descriptor=expected[0],bounds=list(bounds),source=source.hex()))
assert len(checks)==9
r=dict(result='PASS_RAW_SUPPLEMENTAL_REGION_CONSTRUCTION',records=len(checks),checks=checks,disabled_flag_rejected=True,scope='Raw objectflag/descriptor and current region bounds exactly reconstruct9originalsupplementalrecords; object association traversal remains original.')
(p/'owned-supplemental-region-tests.json').write_text(json.dumps(r,indent=2));print(r['result'],[(x['object_index'],x['descriptor']) for x in checks])
