"""Temporal sky/world/final stage attribution; historical backend scope explicit."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
folder=Path(sys.argv[1]);m=json.loads((folder/'manifest.json').read_text())
assert len(m['rows'])==48 and not m['missed'] and not m['pending']
previous={};results=[]
def read(row):
 data=(folder/row['pixel_file']).read_bytes()
 assert len(data)==3240*64*4 and hashlib.sha256(data).hexdigest()==row['pixel_sha256']
 return np.frombuffer(data,np.uint8).reshape(64,3240,4).copy()
for r in m['rows']:
 assert r['native_result']==1 and r['publication'][:3]==[r['epoch'],r['generation'],r['index']]
 assert r['commit'][:5]==[r['epoch'],r['generation'],r['source_older'],r['source_newer'],r['index']]
 stage,world,final=read(r),read(r['world_capture']),read(r['final_capture'])
 for part in (r['world_capture'],r['final_capture']):
  assert [part[k] for k in ('epoch','generation','index','capture_id','y')]==[r[k] for k in ('epoch','generation','index','capture_id','y')]
 assert r['sky_stage_capture_ns']<=r['world_capture']['capture_ns']<=r['final_capture']['capture_begin_ns']<=r['commit'][6]
 old=previous.get(r['y'])
 if old:
  a,old_stage,old_world,old_final=old
  assert a['index']+1==r['index'] and (a['epoch'],a['generation'])==(r['epoch'],r['generation'])
  moving=np.max(np.abs(stage[:,:,:3].astype(np.int16)-old_stage[:,:,:3].astype(np.int16)),axis=2)>2
  held=moving & np.all(final==old_final,axis=2)
  changed_by_world=np.any(world!=stage,axis=2)|np.any(old_world!=old_stage,axis=2)
  changed_by_hud=np.any(final!=world,axis=2)|np.any(old_final!=old_world,axis=2)
  results.append(dict(y=r['y'],index=r['index'],moving_sky_stage_pixels=int(moving.sum()),held_final_with_moving_stage=int(held.sum()),held_with_world_change=int((held&changed_by_world).sum()),held_with_hud_change=int((held&changed_by_hud).sum()),held_without_any_later_stage_change=int((held&~changed_by_world&~changed_by_hud).sum())))
 previous[r['y']]=r,stage,world,final
assert len(results)==42 and all(r['held_without_any_later_stage_change']==0 for r in results)
out=dict(result='PASS_HISTORICAL_STAGE_TEMPORAL_ATTRIBUTION',source=str(folder.resolve()),backend=m['rows'][0]['backend'],transitions=results,held_final_with_moving_stage=sum(r['held_final_with_moving_stage'] for r in results),unexplained_without_later_stage_change=0,scope='Historical three-stage backend, not current linear renderer. Same-coordinate sky-stage motion and later world/HUD changes explain final holds by pixel-stage differences; no exclusive geometry ownership or physical cadence proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='transitions'})
