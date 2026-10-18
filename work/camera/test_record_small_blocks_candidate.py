import json,gc
from pathlib import Path
from owned_motion_pairs import _decode_records as reference
from owned_record_small_blocks_candidate import decode_records
checks=0;rows=[]
for stamp in ('1791539869506441500','1791566914177935300'):
 report=json.loads(Path('work/camera/prototype-runs/owned-native-'+stamp+'.json').read_text())
 folder=Path('work/camera/prototype-runs/fullscene-failure-1791566912183939000') if stamp=='1791566914177935300' else Path(report['live_preparation_profiles'][0]['capture'])
 source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
 ns={};exec(compile(source,'fixture-setup','exec'),ns)
 try:
  for frame in ns['frames']:
   a=reference(frame);b=decode_records(frame)
   assert {k:v for k,v in a.items() if k!='records'}=={k:v for k,v in b.items() if k!='records'}
   assert len(a['records'])==len(b['records'])
   for x,y in zip(a['records'],b['records']):
    assert x['kind']==y['kind'] and x['context']==y['context'] and x['key']==y['key']
    assert list(map(bytes,x['blocks']))==list(map(bytes,y['blocks']))
    assert all((type(v) is bytes and not gc.is_tracked(v)) if len(v)<=256 else isinstance(v,memoryview) for v in y['blocks'])
    checks+=12
   rows.append(dict(fixture=stamp,refresh=a['refresh'],records=len(a['records']),copied_payload_bytes=sum(len(v) for r in b['records'] for v in r['blocks'] if type(v) is bytes),reference_tracked_blocks=sum(gc.is_tracked(v) for r in a['records'] for v in r['blocks']),candidate_tracked_blocks=sum(gc.is_tracked(v) for r in b['records'] for v in r['blocks'])))
 finally:ns['prepared'].close();ns['history'].close()
out=dict(result='PASS_EXACT_SMALL_BLOCK_COMPONENT',block_checks=checks,rows=rows,scope='Four captured frames exact payload/identity parity; small copied bytes untracked; large blocks remain shared memoryviews. No renderer/spawn/performance qualification; payload copying costs unmeasured.')
Path('work/camera/prototype-runs/record-small-blocks-20261009.json').write_text(json.dumps(out,indent=2));print(out)
