import json, hashlib, sys
from pathlib import Path
import numpy as np
folder=Path(sys.argv[1]); m=json.loads((folder/'manifest.json').read_text())
assert len(m['rows'])==48 and not m['missed'] and not m['pending']
previous={}; transitions=[]
for r in m['rows']:
 assert r['commit'][:5]==[r['epoch'],r['generation'],r['source_older'],r['source_newer'],r['index']]
 planes=[]
 for name,key in [(r['pixel_file'],'pixel_sha256'),(r['final_capture']['pixel_file'],None),(r['coverage_file'],'coverage_sha256')]:
  data=(folder/name).read_bytes(); expected=r['final_capture']['pixel_sha256'] if key is None else r[key]
  assert hashlib.sha256(data).hexdigest()==expected
  planes.append(np.frombuffer(data,np.uint8))
 stage,final,mask=planes;stage=stage.reshape(64,3240,4);final=final.reshape(64,3240,4);mask=mask.reshape(64,3240)==255
 assert not np.any(mask & np.any(stage!=final,axis=2))
 for n in range(2):
  data=(folder/(str(r['sequence'])+'.input'+str(n)+'.rgba')).read_bytes()
  assert len(data)==240*160*4 and hashlib.sha256(data).hexdigest()==r['input'+str(n)+'_sha256']
 inputs=(r['sky_weight'],r['input0_sha256'],r['input1_sha256'])
 if r['y'] in previous:
  old,os,of,om,oi=previous[r['y']]
  assert old['index']+1==r['index'] and (old['epoch'],old['generation'])==(r['epoch'],r['generation'])
  changed=inputs!=oi; pixel_changed=bool(np.any(stage!=os))
  assert changed or not pixel_changed, 'Identical sky input produced changing sky stage'
  visible=mask & om
  transitions.append(dict(index=r['index'],y=r['y'],inputs_changed=changed,sky_stage_changed=pixel_changed,visible_pixels=int(visible.sum()),visible_final_changed_pixels=int(np.count_nonzero(visible & np.any(final!=of,axis=2))),commit_interval_ms=(r['commit'][6]-old['commit'][6])/1e6))
 previous[r['y']]=r,stage,final,mask,inputs
out=dict(result='PASS_EXACT_SKY_INPUT_PIXEL_CLASSIFICATION',frames=48,transitions=transitions,moving_input_transitions=sum(t['inputs_changed'] for t in transitions),moving_input_held_stage=sum(t['inputs_changed'] and not t['sky_stage_changed'] for t in transitions),stationary_input_transitions=sum(not t['inputs_changed'] for t in transitions),scope='Retrospective bounded six-band capture; input identity includes both exact RGBA input planes and blend weight. Does not prove sustained or physical 60-fps gameplay.')
(folder/'sky-input-pixel-classification.json').write_text(json.dumps(out,indent=2))
print(json.dumps({k:v for k,v in out.items() if k!='transitions'}))
