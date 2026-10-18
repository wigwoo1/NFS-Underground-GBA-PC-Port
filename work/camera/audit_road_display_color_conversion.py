from pathlib import Path
import struct,json
p=Path('work/camera');rgb=(p/'prototype-runs/racing-motion-audit-a88232ac136d4ad58dc7231b706de812-complete-stable-rgb.bin').read_bytes();pal=(p/'stable-road-display-palettes.bin').read_bytes();last={}
for cmd in (3,4,7):
 samples=(p/f'stable-road-{cmd}-all-original-samples.bin').read_bytes()
 for offset in range(0,len(samples),5):dest,index=struct.unpack_from('<IB',samples,offset);last[dest]=index
counts=dict(floor=0,replicate=0,both=0,neither=0,distinguishing_floor=0,distinguishing_replicate=0)
for dest,index in last.items():
 y,x=divmod(dest,240);px=int(300+(x+.5)*13.5);py=int((y+.5)*13.5);word=struct.unpack_from('<H',pal,y*512+index*2)[0];values=[(word>>(k*5))&31 for k in range(3)];floor=bytes(v*255//31 for v in values);repeat=bytes((v<<3)|(v>>2) for v in values);offset=(py*3840+px)*3;actual=rgb[offset:offset+3];a=actual==floor;b=actual==repeat
 counts['floor']+=a;counts['replicate']+=b;counts['both']+=a and b;counts['neither']+=not(a or b);counts['distinguishing_floor']+=a and not b;counts['distinguishing_replicate']+=b and not a
report=dict(result='DIAGNOSTIC',counts=counts,scope='Road last-write indices and retained scanline palettes versus sourcepixel centers in retained4K stable native previewRGB. Existing renderer output is NOT independent original framebuffer oracle; other geometry/HUD/effects can occlude.');(p/'road-display-color-conversion-audit.json').write_text(json.dumps(report,indent=2));print(report)
