"""Audit every saved live sky transition; visibility is not inferred from phase metadata."""
import json,sys
from pathlib import Path
import numpy as np
root=Path('work/camera/prototype-runs')
x=np.floor((np.arange(3240,dtype=np.float32)+.5)*np.float32(2/27)).astype(int)
y=np.floor((np.arange(594,1458,27,dtype=np.float32)+.5)*np.float32(2/27)).astype(int)
reports=[];excluded=[]
for manifest in sorted(root.glob('linear-sky-pixels-*/manifest.json')):
 rows=json.loads(manifest.read_text())['rows'];previous=None;transitions=[];minimum=None
 if not rows:
  excluded.append(dict(manifest=str(manifest),reason='empty capture'));continue
 with np.load(rows[0]['file']) as first:
  if first['actual'].shape!=(32,3240,4):
   excluded.append(dict(manifest=str(manifest),reason='historical crop differs; coordinates unverified',shape=list(first['actual'].shape)));continue
 for row in rows:
  with np.load(row['file']) as data:
   actual=data['actual'].copy();lo=data['lower'][y[:,None],x[None,:]];hi=data['upper'][y[:,None],x[None,:]]
  assert actual.shape==(32,3240,4) and 0<=row['phase']<=1
  expected=np.rint(lo.astype(float)+(hi.astype(float)-lo.astype(float))*np.float32(row['phase'])).astype(np.uint8)
  opaque=(lo[:,:,3]>127)&(hi[:,:,3]>127)
  match=np.all(np.abs(actual.astype(np.int16)-expected.astype(np.int16))<=1,axis=2)&opaque
  assert row['native_result']==1 and row['commit'][:2]==row['identity'][:2] and row['commit'][4]==row['identity'][2]
  minimum=int(match.sum()) if minimum is None else min(minimum,int(match.sum()))
  if previous:
   prior,old_actual,old_expected,old_match=previous
   if row['identity'][:2]==prior['identity'][:2] and row['identity'][2]==prior['identity'][2]+1:
    jointly_visible=match&old_match
    # Only oracle changes exceeding the combined rounding tolerance can prove a hold.
    expected_motion=(np.max(np.abs(expected.astype(np.int16)-old_expected.astype(np.int16)),axis=2)>2)&jointly_visible
    actual_motion=np.any(actual!=old_actual,axis=2)&expected_motion
    transitions.append(dict(from_index=prior['identity'][2],to_index=row['identity'][2],jointly_matching_pixels=int(jointly_visible.sum()),unambiguous_expected_motion_pixels=int(expected_motion.sum()),observed_motion_pixels=int(actual_motion.sum()),unexplained_held_pixels=int((expected_motion&~actual_motion).sum()),phase_changed=row['phase']!=prior['phase']))
  previous=row,actual,expected,match
 observable=[t for t in transitions if t['unambiguous_expected_motion_pixels']>0]
 # Matching pixels demonstrate bounded motion only; changing occlusion prevents a full-sky hold verdict.
 reports.append(dict(manifest=str(manifest),frames=len(rows),minimum_matching_pixels=minimum,transitions=transitions,observable_transitions=len(observable),unobservable_transitions=len(transitions)-len(observable)))
assert reports
out=dict(result='ANALYZED_BOUNDED_SAVED_SKY_MOTION',captures=reports,excluded=excluded,observable_transitions=sum(r['observable_transitions'] for r in reports),unobservable_transitions=sum(r['unobservable_transitions'] for r in reports),scope='All adjacent successful commit captures in saved bounded synchronous windows. Both frames must match the independent source-color oracle within one channel value; changes must exceed combined rounding tolerance. Unmatched or occluded pixels are unverified. No realtime cadence, physical scanout, or full-scene fidelity claim.')
Path(sys.argv[1]).write_text(json.dumps(out,indent=2));print(out['result'],len(reports),'captures',out['observable_transitions'],'observable',out['unobservable_transitions'],'unobservable')
