"""Single identity, earlier-owned static candidate experiment; never live policy."""
from pathlib import Path
import struct,json
p=Path('work/camera')
def read(serial):
 b=(p/f'order-boundary-{serial}.bin').read_bytes();return b,{t:bytearray(b[o:o+n]) for t,o,n in [struct.unpack_from('<3I',b,32+i*12) for i in range(5)]}
a,s=read(140);ident=(2,50331840,139937176,37,0);n=struct.unpack_from('<I',s[2],4)[0]
assert ident not in [struct.unpack_from('<5I',s[5],8+i*20) for i in range(n)]
surface=(p/'candidate-at-publication-140.bin').read_bytes()
count,w,h=struct.unpack_from('<3I',surface);assert len(surface)==12+count*40+w*h*4
found=(surface,bytes(4)) # Checked bridge supports only unlit candidates.
s[2]+=found[0];struct.pack_into('<I',s[2],4,n+1)
s[3]+=struct.pack('<I',n);struct.pack_into('<I',s[3],4,n+2)
s[4]=s[4][:-131072]+found[1]+s[4][-131072:];struct.pack_into('<I',s[4],4,n+1)
s[5]=s[5][:-20]+struct.pack('<5I',*ident)+s[5][-20:];struct.pack_into('<I',s[5],4,n+2)
out=bytearray(a[:96])
for tag in range(1,6):
 out+=bytes((-len(out))%8);offset=len(out);out+=s[tag];struct.pack_into('<3I',out,32+(tag-1)*12,tag,offset,len(s[tag]))
struct.pack_into('<I',out,8,len(out));(p/'candidate-140.bin').write_bytes(out)
(p/'candidate-140.json').write_text(json.dumps(dict(identity=ident,source_serial=140,target_serial=140,scope='Candidate extracted inside scene140 publication callback before scene141 exists. Supplied research identity; no automatic candidate selection.'),indent=2))
