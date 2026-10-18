from pathlib import Path
import json,struct,collections
from scene_batches import records
root=Path('work/camera');active=None;counts=collections.Counter();levels=collections.Counter();source_pairs=collections.Counter();per_wall={};lod=0;events=0
for e in records(root/'shading-spans.bin'):
 events+=1
 if e['pc']==0x03000304:active=e
 if e['pc'] not in (0x03005320,0x030053e8):continue
 if active is None:continue # Capture may attach partway through a wall.
 flags=active['regs'][2];shaded=e['pc']==0x03005320
 assert shaded==(not bool(flags&256)),(e['id'],flags,e['pc'])
 data=e['blocks'][75][1];counts['shaded' if shaded else 'unshaded']+=1
 if shaded:
  level=struct.unpack_from('<h',data,42)[0];assert 0<=level<16
  table=struct.unpack_from('<I',data,20)[0];assert table==active['blocks'][74][0]
  source=active['blocks'][5][1]
  source_pairs[f'{source[60]},{source[61]}->{level}']+=1
  levels[level]+=1;per_wall.setdefault(active['id'],set()).add(level)
 if struct.unpack_from('<I',data,24)[0] and struct.unpack_from('<I',data,44)[0]>0x1b000:lod+=1
assert counts and events<20000,'Capture may be truncated'
report={'result':'PASS','events':events,'span_routes':dict(counts),'shade_levels':dict(sorted(levels.items())),'source_to_span_shades':dict(source_pairs),'shaded_walls':len(per_wall),'walls_with_varying_shade':sum(len(v)>1 for v in per_wall.values()),'reduced_LOD_spans':lod,'scope':'Live dispatch flag, shade-table pointer and valid shade range; interpolation formula still unresolved.'}
(root/'wall-span-tests.json').write_text(json.dumps(report,indent=2));print(report)
