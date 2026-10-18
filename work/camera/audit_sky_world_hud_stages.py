import json,sys
from pathlib import Path
import numpy as np
p=Path(sys.argv[1]);m=json.loads((p/'manifest.json').read_text());rows=[];motions=[];previous=None
for i,r in enumerate(m['rows']):
 def image(name):return np.frombuffer((p/name).read_bytes(),np.uint8).reshape(r['band_height'],3840,4)[:,300:3540,:3]
 sky=image(str(i)+'.sky-stage.rgba');world=image(str(i)+'.world-stage.rgba');final=image(r['file'])
 world_changed=np.any(world!=sky,axis=2);hud_changed=np.any(final!=world,axis=2)
 rows.append(dict(draw=r['draw_number'],pixels=world_changed.size,world_changes=int(world_changed.sum()),hud_changes=int(hud_changed.sum()),sky_preserved_by_world=int((~world_changed).sum()),sky_preserved_in_final=int(np.all(final==sky,axis=2).sum()),hud_replaces_world_preserved_sky=int((hud_changed&~world_changed).sum())))
 visible=np.all(final==sky,axis=2)&~world_changed
 if previous is not None:
  old_sky,old_final,old_visible=previous
  moving=np.any(sky!=old_sky,axis=2)&visible&old_visible
  motions.append(dict(draw=r['draw_number'],joint_visible_sky=int((visible&old_visible).sum()),moving_sky_surviving_final=int(moving.sum()),actual_final_changes=int((moving&np.any(final!=old_final,axis=2)).sum())))
 previous=sky.copy(),final.copy(),visible.copy()
out=dict(rows=rows,motions=motions,scope='Exact same-frame RGB differences after actual ordered sky/world/HUD draws. Coincident geometry colors possible. Does not prove semantic geometry coverage or physical scanout cadence.')
(p/'world-hud-stage-audit.json').write_text(json.dumps(out,indent=2))
print({k:[min(r[k] for r in rows),max(r[k] for r in rows)] for k in ['world_changes','hud_changes','sky_preserved_by_world','sky_preserved_in_final','hud_replaces_world_preserved_sky']})
print('visible moving transitions',sum(r['moving_sky_surviving_final']>0 for r in motions),'of',len(motions))
