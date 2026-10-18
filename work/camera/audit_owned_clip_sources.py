from pathlib import Path
import struct,json,collections
from owned_motion_pairs import records,plan_pair
p=Path('work/camera');files=sorted((p/'motion-actual-scanline-assets').glob('*-native-complete-frame.bin'));counts={k:collections.Counter() for k in (1,2,3)};scenes=[];changed=[]
for f in files:
 raw=f.read_bytes();scene=records(raw);scenes.append((raw,scene))
 for r in scene['records']:
  b=r['blocks'];rect=struct.unpack('<4i',b[9]) if r['kind']==3 else struct.unpack('<4H',b[5]);counts[r['kind']][rect]+=1
for (a,sa),(b,sb) in zip(scenes,scenes[1:]):
 if sa['ticks']>=sb['ticks']:continue
 plan=plan_pair(a,b)
 for i,j in plan['pairs']:
  x=sa['records'][i];y=sb['records'][j];idx=9 if x['kind']==3 else 5
  if bytes(x['blocks'][idx])!=bytes(y['blocks'][idx]):changed.append(dict(older=sa['refresh'],newer=sb['refresh'],kind=x['kind'],context=x['context']))
r=dict(result='CLIP_SOURCE_INVENTORY',scenes=len(scenes),bounds={str(k):[dict(rect=list(rect),draws=n) for rect,n in c.items()] for k,c in counts.items()},paired_bounds_changes=changed,scope='Raw captured source clip bounds; inventory alone does not establish semantics outside captured interval.')
(p/'owned-clip-source-audit.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
