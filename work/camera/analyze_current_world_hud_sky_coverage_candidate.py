import hashlib,json,sys
from pathlib import Path
import numpy as np
folder=Path(sys.argv[1]);m=json.loads((folder/'manifest.json').read_text());assert len(m['rows'])==32 and m['pending']==0
rows=[];transitions=[];previous=None
x=np.arange(3840)+.5;tx=np.clip(np.floor((x-300)/13.5).astype(int),0,239);ty=np.floor((np.arange(648,664)+.5)/13.5).astype(int)
valid=np.broadcast_to((x>=300)&(x<3540),(16,3840))
for i,r in enumerate(m['rows']):
 assert r['backend']=='owned-d3d-current-world-stage-candidate.dll' and r['native_result']==1 and r['present']['status']==0
 assert r['commit'][:5]==[r['epoch'],r['generation'],r['source_older'],r['source_newer'],r['index']]
 assert r['present']['thread']==r['thread'] and r['read_end_ns']<=r['present']['completed_ns']<=r['commit'][6]
 data=(folder/r['strip_file']).read_bytes();assert hashlib.sha256(data).hexdigest()==r['strip_sha256']
 final=np.frombuffer(data,np.uint8).reshape(16,3840,4)[:,:,:3]
 sky=np.frombuffer((folder/(str(i)+'.stage.rgba')).read_bytes(),np.uint8).reshape(16,3840,4)[:,:,:3]
 world=np.frombuffer((folder/(str(i)+'.world.rgba')).read_bytes(),np.uint8).reshape(16,3840,4)[:,:,:3]
 hud=[np.frombuffer((folder/(str(i)+'.hud'+str(slot)+'.rgba')).read_bytes(),np.uint8).reshape(160,240,4)[ty[:,None],tx[None,:]] for slot in range(3)]
 world_modified=valid&np.any(world!=sky,axis=2);hud_modified=valid&np.any(final!=world,axis=2)
 flags=hud[1][:,:,2];control=np.where(flags>=128,flags&63,63)
 rows.append(dict(index=r['index'],world_modified_pixels=int(world_modified.sum()),hud_modified_pixels=int(hud_modified.sum()),final_equals_sky_pixels=int((valid&np.all(final==sky,axis=2)).sum()),hud_modified_object_candidate_pixels=int((hud_modified&(hud[0][:,:,3]>127)).sum()),hud_modified_text_pixels=int((hud_modified&(hud[2][:,:,3]>127)).sum()),hud_modified_background_disabled_pixels=int((hud_modified&((control&4)==0)).sum())))
 if previous is not None:
  a,old_sky,old_world,old_final=previous;moving=valid&np.any(sky!=old_sky,axis=2)
  world_kept=moving&np.all(world==sky,axis=2)&np.all(old_world==old_sky,axis=2)
  final_kept=world_kept&np.all(final==world,axis=2)&np.all(old_final==old_world,axis=2)
  transitions.append(dict(previous=a['index'],current=r['index'],sky_changed_pixels=int(moving.sum()),world_preserved_moving_sky_pixels=int(world_kept.sum()),final_preserved_moving_sky_pixels=int(final_kept.sum())))
 previous=r,sky.copy(),world.copy(),final.copy()
out=dict(result='PASS_CURRENT_SKY_WORLD_HUD_PHASE_DIFFERENCES',rows=rows,transitions=transitions,scope='Exact same-frame RGB differences before/after ordered world/HUD passes in sampled band. No exclusive geometry ownership when colors coincide, no all-sky/scanout/60fps proof. HUD source flags counted, not full priority/effect classification.')
(folder/'world-hud-coverage-audit.json').write_text(json.dumps(out,indent=2));print(dict(result=out['result'],samples=len(rows),world_modified_range=[min(r['world_modified_pixels'] for r in rows),max(r['world_modified_pixels'] for r in rows)],hud_modified_range=[min(r['hud_modified_pixels'] for r in rows),max(r['hud_modified_pixels'] for r in rows)],world_motion_transitions=sum(t['world_preserved_moving_sky_pixels']>0 for t in transitions),final_motion_transitions=sum(t['final_preserved_moving_sky_pixels']>0 for t in transitions)))
