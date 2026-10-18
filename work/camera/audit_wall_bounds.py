from pathlib import Path
import struct,json
from scene_batches import records
root=Path('work/camera');walls=[];active=None
for event in records(root/'shading-spans.bin'):
 if event['pc']==0x03000304:
  edge=struct.unpack_from('<2h',event['blocks'][6][1]);bounds=struct.unpack_from('<4H',event['blocks'][1][1],0xe2)
  left=edge[0]>>1;right=(edge[1]+1)>>1;count=right-left;reject=count<=1
  if left<bounds[0]>>1:
   if right<bounds[0]>>1:reject=True
   left=bounds[0]>>1;count=right-left
  if right>bounds[1]>>1:
   if left>bounds[1]>>1:reject=True
   right=bounds[1]>>1;count=right-left+1
  active=dict(event=event['id'],source=hex(event['blocks'][5][0]),edge=list(edge),bounds=list(bounds),
              expected=[] if reject or count<=1 else list(range(left,left+count)),actual=[])
  walls.append(active)
 elif event['pc'] in (0x03005320,0x030053e8) and active is not None:
  dest=event['regs'][1];active['actual'].append((dest-(0x0600a000 if dest>=0x0600a000 else 0x06000000))//2)
# Trace can stop within the final wall when the bounded event limit is reached.
complete=walls[:-1];mismatches=[w for w in complete if w['expected']!=w['actual']]
report=dict(wall_entries=len(walls),complete_walls=len(complete),exact_dispatch_matches=len(complete)-len(mismatches),
 mismatch_examples=mismatches[:8],scene0_building=next(w for w in walls if w['source']=='0x85744cc'),
 scope='Original horizontal column bounds from captured state +0xE2/+0xE4. These per-draw bounds must not be frozen or interpolated as screen polygons for moving-camera rendering.')
(root/'wall-bounds-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
