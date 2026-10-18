from pathlib import Path
import struct,json
from scene_batches import records
p=Path('work/camera');old=list(records(p/'motion-original-video-state-world.bin'));new=list(records(p/'motion-original-actual-rgb-world.bin'));assert old==new
checks=[];ends=[8757,8761,8765,8768,8772,8775,8779];nexts=ends[1:]+[8782]
for end,nxt in zip(ends,nexts):
 expected=struct.unpack('<38400I',(p/f'motion-static-rgb-assets/{end}-rgb.bin').read_bytes());candidates=[]
 for refresh in range(end,nxt):
  actual=struct.unpack('<38400I',(p/f'motion-actual-rgb-assets/{refresh}-rgb.bin').read_bytes());different=sum((a&0xffffff)!=b for a,b in zip(actual,expected));candidates.append(dict(refresh=refresh,different_pixels=different,exact=different==0))
 checks.append(dict(flip_refresh=end,candidates=candidates))
report=dict(result='AUDITED_ACTUAL_VS_STATIC_RGB',existing_records_preserved=len(old),checks=checks,scope='Actual completed refresh RGB compared with static closing snapshot within observed next-flip interval. No screen-polygon geometry inference or timing interpolation.')
(p/'motion-actual-rgb-tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(report)
