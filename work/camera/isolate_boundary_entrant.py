"""Hide only the identified entrant in a private diagnostic packet."""
from pathlib import Path
import struct,json
p=Path('work/camera');b=bytearray((p/'boundary-fixed-material-141.bin').read_bytes());original=bytes(b)
sections={t:(o,n) for t,o,n in [struct.unpack_from('<3I',b,32+i*12) for i in range(5)]}
wo,wn=sections[2];io,_=sections[5];pos=wo+8;changed=[];matches=0
for i in range(struct.unpack_from('<I',b,wo+4)[0]):
 v,w,h=struct.unpack_from('<3I',b,pos);start=pos+12+v*40;end=start+w*h*4
 ident=struct.unpack_from('<5I',b,io+8+i*20)
 if ident==(2,50331840,139937176,37,0):
  matches+=1
  for offset in range(start+3,end,4):
   if b[offset]:changed.append(offset);b[offset]=0
 pos=end
assert matches==1 and pos==wo+wn
check=bytearray(b)
for offset in changed:check[offset]=original[offset]
assert check==original
(p/'boundary-hidden-entrant-141.bin').write_bytes(b)
(p/'entrant-isolation.json').write_text(json.dumps(dict(matches=matches,alpha_bytes_changed=len(changed),scope='Diagnostic-only alpha suppression of one recovered world identity; not a visibility fix.'),indent=2))
