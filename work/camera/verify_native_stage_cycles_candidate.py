"""Whole-run scalar ownership/serial validation; not visible cadence certification."""
import json,sys,copy
from pathlib import Path
def validate(d,live):
 rows=d['rows'];assert len(rows)==live['dxgi_display_progress']['queries'] and len(rows)<=d['capacity']
 owners={};previous=None
 for r in rows:
  key=tuple(r['identity']);v=r['values'];assert key not in owners and len(v)==12
  assert v[0]<=v[1] and v[2]<=v[3] and v[6]<=v[7] and v[8]<=v[9] and v[5]>0 and v[11]>0
  if previous:assert v[5]>previous[5] and v[11]>previous[11]
  previous=v;owners[key]=v
 for r in live['presentation_samples']:
  x=r['native_transaction']['native_stage_cycles_present'];assert owners[tuple(x['identity'])]==x['values']
 return dict(result='PASS_COMPLETE_OWNER_STAGE_RECORDS',rows=len(rows),retained_transaction_matches=len(live['presentation_samples']),max_pump_ms=max((r['values'][1]-r['values'][0])/1e6 for r in rows),max_last_world_batch_ms=max((r['values'][7]-r['values'][6])/1e6 for r in rows),scope=d['scope'])
if __name__=='__main__':
 d=json.loads(Path(sys.argv[1]).read_text());live=json.loads(Path(sys.argv[2]).read_text());report=validate(d,live)
 bad=copy.deepcopy(d);bad['rows'][1]['identity']=bad['rows'][0]['identity']
 try:validate(bad,live)
 except AssertionError:report['duplicate_owner_negative_control']='PASS'
 else:raise AssertionError('Duplicate owner accepted')
 bad=copy.deepcopy(d);bad['rows'][1]['values'][5]=bad['rows'][0]['values'][5]
 try:validate(bad,live)
 except AssertionError:report['stale_serial_negative_control']='PASS'
 else:raise AssertionError('Stale serial accepted')
 Path(sys.argv[3]).write_text(json.dumps(report,indent=2));print(report)
