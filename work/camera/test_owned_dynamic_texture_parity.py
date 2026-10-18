from pathlib import Path
import struct,json
from owned_motion_pairs import records
p=Path('work/camera');reference=[]
for file in (p/'motion-actual-scanline-assets').glob('*-native-complete-frame.bin'):
 frame=records(file.read_bytes());camera=next(bytes(r['blocks'][4 if r['kind']==1 else 3]) for r in frame['records'] if r['kind'] in (1,2))
 for r in frame['records']:
  if r['kind']==3:reference.append((frame['refresh'],camera,bytes(r['blocks'][10])))
raw=(p/'owned-object-textures.bin').read_bytes();offset=0;checks=[]
while offset<len(raw):
 h=struct.unpack_from('<12I',raw,offset);camera=raw[offset+500:offset+548];texture=raw[offset+548:offset+548+h[9]];matches=[refresh for refresh,ca,t in reference if ca==camera and t==texture];assert len(matches)==1,(h[1],matches)
 checks.append(dict(capture_refresh=h[1],closed_frame=matches[0],bytes=h[9]));offset+=548+h[9]
assert len(checks)==7
r=dict(result='PASS_DYNAMIC_TEXTURE_DRAW_PARITY',scenes=7,bytes_exact=sum(x['bytes'] for x in checks),checks=checks,scope='Independent source texture capture matches previously verified owned model draw packets; fullscene motion still pending.')
(p/'owned-dynamic-texture-parity.json').write_text(json.dumps(r,indent=2));print(r['result'],r['scenes'],r['bytes_exact'])
