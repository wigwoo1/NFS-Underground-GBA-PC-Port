import json,sys,hashlib,copy
from pathlib import Path
import numpy as np
def owners(manifest,tail):
 rows=manifest['rows'];assert len(rows)==manifest['expected']==12 and not manifest['missed'] and manifest['pending']==0
 lookup={tuple(x['identity']):x for x in tail['rows']};assert len(lookup)==len(tail['rows'])
 for n,row in enumerate(rows):
  assert row['sequence']==n and row['identity'][2]==manifest['start_index']+n
  assert row['native_result']==1 and row['commit'][:2]==row['identity'][:2] and row['commit'][4]==row['identity'][2] and row['commit'][2:4]==[row['older'],row['newer']]
  assert row['width']==3840 and row['height']==2160 and row['thread']==row['poll_thread']
  assert row['capture_begin_ns']<=row['capture_end_ns']<=row['poll_begin_ns']<=row['poll_end_ns']
  assert lookup[tuple(row['identity'])]['commit_ns']==row['commit'][6]
 return rows
m=json.loads(Path(sys.argv[1]).read_text());t=json.loads(Path(sys.argv[2]).read_text());rows=owners(m,t)
bad=copy.deepcopy(m);bad['rows'][0]['identity'][2]+=1
try:owners(bad,t)
except AssertionError:pass
else:raise AssertionError('Wrong identity accepted')
previous=None;transitions=[]
for row in rows:
 data=Path(row['file']).read_bytes();assert len(data)==3840*2160*4 and hashlib.sha256(data).hexdigest()==row['sha256'];im=np.frombuffer(data,np.uint8).reshape(2160,3840,4)
 if previous is not None:
  p,old=previous;assert row['identity'][:2]==p['identity'][:2] and row['identity'][2]==p['identity'][2]+1
  changed=np.max(np.abs(im[:,:,:3].astype(np.int16)-old[:,:,:3].astype(np.int16)),axis=2)>2
  transitions.append(dict(older=p['identity'],newer=row['identity'],changed_pixels=int(changed.sum()),tiles=[[int(changed[y:y+720,x:x+1280].sum()) for x in (0,1280,2560)] for y in (0,720,1440)],commit_interval_ms=(row['commit'][6]-p['commit'][6])/1e6))
 previous=(row,im)
out=dict(result='PASS_EXACT_COMPLETE_4K_ASYNC_CAPTURE_SEQUENCE',frames=len(rows),transitions=transitions,held_entire_frames=sum(x['changed_pixels']==0 for x in transitions),max_capture_ms=max((x['capture_end_ns']-x['capture_begin_ns'])/1e6 for x in rows),max_poll_ms=max((x['poll_end_ns']-x['poll_begin_ns'])/1e6 for x in rows),wrong_identity_negative_control=True,scope='All pixels in twelve entire native4K render-target captures; exact whole-run commit identity join, RGBthreshold2 and nine spatial regions. Short observed sequence only; tiles do not establish semantic-layer fidelity, route coverage, physical scanout or sustained60.')
Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print(json.dumps(out))
