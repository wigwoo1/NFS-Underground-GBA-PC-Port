from pathlib import Path
import struct,json
from owned_motion_pairs import records
p=Path('work/camera');target=bytes(records((p/'motion-actual-scanline-assets/8758-native-complete-frame.bin').read_bytes())['records'][18]['blocks'][0][:68]);raw=(p/'owned-wall-owners.bin').read_bytes();matches=[]
for o in range(0,len(raw),484):
 h=struct.unpack_from('<16I',raw,o)
 if raw[o+64:o+132]==target:matches.append(dict(refresh=h[1],descriptor_index=(h[6]-h[11])//48,source=hex(h[3]),owner_count=h[5]))
assert len(matches)==1 and matches[0]['descriptor_index']==90
print('PASS_UNMATCHED_WALL_OWNER',matches)
