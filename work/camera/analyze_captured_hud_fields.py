"""Measure actual retained HUD field changes, without inferring irrelevance."""
import struct,json,collections
from pathlib import Path
p=Path('work/camera');report=json.loads((p/'prototype-runs/owned-native-1791267744113946700.json').read_text());items=report['wall_diagnostic_frames'];rows=[];fields={'registers':(8,104),'affine':(104,128),'obj_vram':(128,32896),'palette':(32896,33920),'oam':(33920,34944)}
previous=None
for item in items:
 data=Path(item['regenerated']).read_bytes();gn,hn=struct.unpack_from('<2I',data,8);assert hn==34944*160;hud=data[40+gn:40+gn+hn]
 if previous is not None:
  counts={k:0 for k in fields};identical=0
  for y in range(160):
   a=previous[y*34944:(y+1)*34944];b=hud[y*34944:(y+1)*34944]
   identical+=a[8:]==b[8:]
   for name,(start,end) in fields.items():counts[name]+=a[start:end]!=b[start:end]
  rows.append(dict(refresh=item['refresh'],identical_visual_rows=identical,changed_rows_by_field=counts))
 previous=hud
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/4k-hud-visual-reuse-20261008');out=dict(result='MEASURED_CAPTURED_HUD_FIELDS',pairs=rows,scope='Exact captured retained bytes excluding refresh/row identity. Field changes not proof of changed final pixels or irrelevant data; no skipped HUD work.')
(cp/'captured-field-changes.json').write_text(json.dumps(out,indent=2));print(rows[:3])
