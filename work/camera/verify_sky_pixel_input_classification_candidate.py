import json,sys,hashlib
from pathlib import Path
folder=Path(sys.argv[1]);m=json.loads((folder/'manifest.json').read_text());rows=m['rows'];assert len(rows)==32 and m['pending']==0
for r in rows:
 assert r['publication'][:3]==[r['epoch'],r['generation'],r['index']]
 assert r['commit'][:5]==[r['epoch'],r['generation'],r['source_older'],r['source_newer'],r['index']]
 assert r['native_result']==1 and r['present']['status']==0 and r['present']['thread']==r['thread']
 assert r['begin_ns']<=r['native_read_end_ns']<=r['end_ns']<=r['present']['end_ns']<=r['commit'][6]
 for field in ['sky','world','sky_stage']:
  assert hashlib.sha256((folder/r[field+'_file']).read_bytes()).hexdigest()==r[field+'_sha256']
transitions=[]
for a,b in zip(rows,rows[1:]):
 if (a['epoch'],a['generation'],a['source_older'],a['source_newer'])!=(b['epoch'],b['generation'],b['source_older'],b['source_newer']):continue
 if a['index']+1!=b['index'] or a['alpha']==b['alpha']:continue
 transitions.append(dict(older=a['source_older'],newer=a['source_newer'],first=a['index'],second=b['index'],changed_sky_pixels=a['sky_stage_sha256']!=b['sky_stage_sha256'],changed_sky_inputs=(a['sky_weight'],a['sky_lower'],a['sky_upper'])!=(b['sky_weight'],b['sky_lower'],b['sky_upper'])))
assert transitions
assert all(x['changed_sky_inputs'] or not x['changed_sky_pixels'] for x in transitions), 'Sky-only pixels changed with identical sky inputs'
out=dict(result='PASS_SKY_PIXEL_OWNERSHIP_AND_INPUT_CLASSIFICATION',samples=len(rows),same_pair_transitions=len(transitions),moving_input_transitions=sum(x['changed_sky_inputs'] for x in transitions),moving_inputs_with_held_pixels=sum(x['changed_sky_inputs'] and not x['changed_sky_pixels'] for x in transitions),stationary_input_transitions=sum(not x['changed_sky_inputs'] for x in transitions),transitions=transitions,scope='Actual current candidate isolated sky-stage pixels before matching native presents, exact source/presentation ownership. Changing alpha alone is not sky movement. Changed-input pixel holds are reported, never silently passed as motion. Readback perturbs timing; no smooth cadence, physical scanout or independent original-game fidelity proof.')
(folder/'ownership-and-input-classification.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='transitions'}))
