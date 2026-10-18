import hashlib,json,sys
from pathlib import Path
import numpy as np
folder=Path(sys.argv[1]);m=json.loads((folder/'manifest.json').read_text());assert len(m['rows'])==48 and not m['missed'] and m['pending']==0
rows=[];transitions=[];previous=None
source=(np.arange(3240,dtype=np.float32)+np.float32(.5))*np.float32(2)/np.float32(27);tx=np.clip(np.floor(source).astype(int),0,239)
for i,r in enumerate(m['rows']):
 assert r['sequence']==i and r['capture_id']==120+i and r['backend']=='owned-d3d-sky-three-stage-transaction-candidate.dll'
 assert r['publication'][:3]==[r['epoch'],r['generation'],r['index']] and r['commit'][:5]==[r['epoch'],r['generation'],r['source_older'],r['source_newer'],r['index']]
 assert r['native_result']==1 and r['present'] is None and r['thread']==r['poll_thread']
 assert r['sky_stage_capture_ns']<=r['capture_begin_ns']<=r['capture_end_ns']<=r['commit'][6]<=r['poll_begin_ns']<=r['poll_end_ns']
 data=(folder/r['pixel_file']).read_bytes();assert len(data)==3240*64*4 and hashlib.sha256(data).hexdigest()==r['pixel_sha256'];final=np.frombuffer(data,np.uint8).reshape(64,3240,4)
 planes=[]
 for slot in range(2):
  data=(folder/(str(i)+'.input'+str(slot)+'.rgba')).read_bytes();assert len(data)==240*160*4 and hashlib.sha256(data).hexdigest()==r['input'+str(slot)+'_sha256'];planes.append(np.frombuffer(data,np.uint8).reshape(160,240,4))
 ty=np.clip(np.floor((np.arange(r['y'],r['y']+64,dtype=np.float32)+np.float32(.5))*np.float32(2)/np.float32(27)).astype(int),0,159)
 lo=planes[0][ty[:,None],tx[None,:]];hi=planes[1][ty[:,None],tx[None,:]];shifted=np.floor(source+np.float32(r['sky_weight']))>np.floor(source)
 # Independent screen-space support overlap, anchored to original edge selection.
 centers=np.arange(3240)+.5;exact_source=centers*2/27;edge=(np.floor(exact_source)+1)*13.5;support=np.minimum(1,edge-centers)
 coverage=np.clip((np.float32(r['sky_weight'])*13.5-(edge-centers-support))/support,0,1)
 blended=np.rint(lo.astype(float)+(hi.astype(float)-lo.astype(float))*coverage[None,:,None]).astype(np.uint8)
 expected=np.where(((lo[:,:,3]>127)&(hi[:,:,3]>127))[:,:,None],blended,np.where(shifted[None,:,None],hi,lo))
 opaque=expected[:,:,3]>127;match=opaque&np.all(np.abs(final[:,:,:3].astype(np.int16)-expected[:,:,:3].astype(np.int16))<=1,axis=2)
 rows.append(dict(index=r['index'],y=r['y'],opaque_reference_pixels=int(opaque.sum()),matching_final_pixels=int(match.sum()),capture_enqueue_ms=(r['capture_end_ns']-r['capture_begin_ns'])/1e6,poll_ms=(r['poll_end_ns']-r['poll_begin_ns'])/1e6))
 if previous is not None:
  a,old_expected,old_match,old_final,old_opaque=previous
  if a['y']==r['y']:
   assert a['index']+1==r['index'] and (a['epoch'],a['generation'])==(r['epoch'],r['generation'])
   moving=opaque&old_opaque&np.any(expected[:,:,:3]!=old_expected[:,:,:3],axis=2);survive=moving&match&old_match
   transitions.append(dict(y=r['y'],previous=a['index'],current=r['index'],expected_changed_pixels=int(moving.sum()),matching_final_changed_pixels=int(survive.sum()),actual_final_changed_pixels=int(np.any(final[:,:,:3]!=old_final[:,:,:3],axis=2).sum())))
 previous=r,expected.copy(),match.copy(),final.copy(),opaque.copy()
assert len(transitions)==42
assert all(x['matching_final_pixels']==x['opaque_reference_pixels'] for x in rows),[(x['index'],x['matching_final_pixels'],x['opaque_reference_pixels']) for x in rows]
out=dict(result='PASS_ALL_OPAQUE_LIVE_SKY_STAGE_PIXELS',samples=len(rows),transitions=transitions,rows=rows,not_ready=m['not_ready'],moving_reference_transitions=sum(t['expected_changed_pixels']>0 for t in transitions),matching_final_motion_transitions=sum(t['matching_final_changed_pixels']>0 for t in transitions),scope='6bands x8frames, native sky-stage capture before world/HUD, source callback phase and successful native commit binding. Every opaque reference pixel matches within1UNORM; transparent background pixels are outside this opaque gate. Not exclusive sky ownership, all-frame/scanout/smooth60 proof; instrumentation perturbs timing.')

pairs=[]
for r in m['rows']:
 f=r['final_capture'];assert [f[k] for k in ('epoch','generation','index','capture_id','y')]==[r[k] for k in ('epoch','generation','index','capture_id','y')]
 assert r['sky_stage_capture_ns']<=f['capture_begin_ns']<=f['capture_end_ns']<=r['commit'][6]<=f['poll_begin_ns']<=f['poll_end_ns']
 assert f['thread']==f['poll_thread']==r['thread']
 data=(folder/f['pixel_file']).read_bytes();assert len(data)==3240*64*4 and hashlib.sha256(data).hexdigest()==f['pixel_sha256']
 final=np.frombuffer(data,np.uint8).reshape(64,3240,4);stage=np.frombuffer((folder/r['pixel_file']).read_bytes(),np.uint8).reshape(64,3240,4)
 changed=np.any(final!=stage,axis=2)
 pairs.append(dict(index=r['index'],y=r['y'],pixels=changed.size,pixels_changed_after_sky=int(changed.sum()),pixels_exactly_preserved=int((~changed).sum())))
world_rows=[]
for r in m['rows']:
 w=r['world_capture'];f=r['final_capture']
 assert [w[k] for k in ('epoch','generation','index','capture_id','y')]==[r[k] for k in ('epoch','generation','index','capture_id','y')]
 assert r['sky_stage_capture_ns']<=w['capture_ns']<=f['capture_begin_ns']<=r['commit'][6]<=w['poll_begin_ns']<=w['poll_end_ns']
 assert w['thread']==w['poll_thread']==r['thread']
 data=(folder/w['pixel_file']).read_bytes();assert len(data)==3240*64*4 and hashlib.sha256(data).hexdigest()==w['pixel_sha256']
 world=np.frombuffer(data,np.uint8).reshape(64,3240,4);stage=np.frombuffer((folder/r['pixel_file']).read_bytes(),np.uint8).reshape(64,3240,4);final=np.frombuffer((folder/f['pixel_file']).read_bytes(),np.uint8).reshape(64,3240,4)
 world_change=np.any(world!=stage,axis=2);hud_change=np.any(final!=world,axis=2)
 world_rows.append(dict(index=r['index'],y=r['y'],world_changed_pixels=int(world_change.sum()),hud_changed_pixels=int(hud_change.sum()),hud_changed_previously_untouched_sky=int((hud_change&~world_change).sum()),world_only_changes=int((world_change&~hud_change).sum())))
out['stage_attribution']=world_rows
out['world_changed_total']=sum(r['world_changed_pixels'] for r in world_rows)
out['hud_changed_total']=sum(r['hud_changed_pixels'] for r in world_rows)
out['hud_changed_untouched_sky_total']=sum(r['hud_changed_previously_untouched_sky'] for r in world_rows)
out['paired_stage_final']=pairs;out['changed_after_sky_total']=sum(x['pixels_changed_after_sky'] for x in pairs);out['paired_pixels_total']=sum(x['pixels'] for x in pairs)
out['scope']='48 sameframe sky/world/final capture triples with nativecommit and timestamp authority. All opaque sky-stage pixels match source oracle within1UNORM. Pixel changes attributed separately to world andHUD stages, notproof their geometry/visibility/effects correct; no scanout60proof.'
(folder/'three-stage-audit.json').write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k not in ('rows','transitions','paired_stage_final','stage_attribution')})
