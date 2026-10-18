import json,sys,hashlib
from pathlib import Path
import numpy as np
src=Path(sys.argv[1]);r=json.loads(src.read_text());assert len(r['rows'])==r.get('expected_captures',48) and not r['missed'] and r['pending']==0
by_band={};transitions=[];excluded=[]
for i,row in enumerate(r['rows']):
 assert row['sequence']==i and row['native_result']==1 and row['commit'][:2]==row['identity'][:2] and row['commit'][4]==row['identity'][2]
 assert row['thread']==row['poll_thread'] and row['poll_begin_ns']>=row['capture_end_ns']
 data=Path(row['file']).read_bytes();assert len(data)==3240*64*4 and hashlib.sha256(data).hexdigest()==row['sha256']
 im=np.frombuffer(data,np.uint8).reshape(64,3240,4)
 old=by_band.get(row['y'])
 if old:
  p,prev=old
  if row['identity'][:2]!=p['identity'][:2] or row['identity'][2]!=p['identity'][2]+1:
   excluded.append(dict(y=row['y'],older=p['identity'],newer=row['identity']));by_band[row['y']]=(row,im);continue
  d=np.max(np.abs(im[:,:,:3].astype(np.int16)-prev[:,:,:3].astype(np.int16)),axis=2)>2
  transitions.append(dict(y=row['y'],older=p['identity'],newer=row['identity'],changed_pixels=int(d.sum()),column_changes=[int(d[:,a:a+1080].sum()) for a in (0,1080,2160)],capture_ms=(row['capture_end_ns']-row['capture_begin_ns'])/1e6,poll_ms=(row['poll_end_ns']-row['poll_begin_ns'])/1e6))
 by_band[row['y']]=(row,im)
assert len(transitions)+len(excluded)==len(r['rows'])-3 and set(by_band)=={216,1080,1944}
assert len(transitions)==45*len(r.get('windows',[300])),'Incomplete consecutive capture window'
out=dict(result='PASS_COMPLETE_ASYNC_SCENE_BAND_CAPTURE',source=str(src.resolve()),captures=len(r['rows']),excluded_window_or_generation_boundaries=excluded,transitions=transitions,not_ready=r['not_ready'],held_bands=sum(t['changed_pixels']==0 for t in transitions),moving_transitions_by_band={y:sum(t['changed_pixels']>0 for t in transitions if t['y']==y) for y in by_band},max_capture_ms=max(t['capture_ms'] for t in transitions),max_poll_ms=max(t['poll_ms'] for t in transitions),scope='Complete bounded3band capture windows withidentity/hash/threadguards; nonadjacent windows/generations explicitlyexcluded. RGBthreshold2; sampledworldregions notsemanticlayer/fidelity/scanout certification.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='transitions'})
