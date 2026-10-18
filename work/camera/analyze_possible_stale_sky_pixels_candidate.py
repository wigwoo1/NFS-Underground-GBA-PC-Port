"""Find possible stale sky pixels without requiring current-frame oracle agreement."""
import json, sys
from pathlib import Path
import numpy as np
root=Path('work/camera/prototype-runs')
x=np.floor((np.arange(3240,dtype=np.float32)+.5)*np.float32(2/27)).astype(int)
y=np.floor((np.arange(594,1458,27,dtype=np.float32)+.5)*np.float32(2/27)).astype(int)
def classify(old_actual, actual, old_expected, expected, old_match, opaque):
    expected_change=np.max(np.abs(expected.astype(np.int16)-old_expected.astype(np.int16)),axis=2)>2
    eligible=old_match & opaque & expected_change
    stale=eligible & np.all(actual==old_actual,axis=2)
    current_match=np.all(np.abs(actual.astype(np.int16)-expected.astype(np.int16))<=1,axis=2)
    return dict(eligible_pixels=int(eligible.sum()),possible_stale_pixels=int(stale.sum()),current_expected_pixels=int((eligible & current_match).sum()),unresolved_pixels=int((eligible & ~current_match).sum()))
# Frozen output must remain eligible even though it fails the current oracle.
a=np.zeros((1,1,4),np.uint8);b=a.copy();b[:,:,0]=10
assert classify(a,a,a,b,np.ones((1,1),bool),np.ones((1,1),bool))['possible_stale_pixels']==1
assert classify(a,b,a,b,np.ones((1,1),bool),np.ones((1,1),bool))['possible_stale_pixels']==0
captures=[];excluded=[]
for path in sorted(root.glob('linear-sky-pixels-*/manifest.json')):
    rows=json.loads(path.read_text())['rows'];previous=None;transitions=[]
    for row in rows:
        with np.load(row['file']) as data:
            actual=data['actual'].copy()
            if actual.shape!=(32,3240,4):
                excluded.append(str(path));break
            lo=data['lower'][y[:,None],x[None,:]];hi=data['upper'][y[:,None],x[None,:]]
        assert row['native_result']==1 and 0<=row['phase']<=1
        assert row['commit'][:2]==row['identity'][:2] and row['commit'][4]==row['identity'][2]
        expected=np.rint(lo.astype(float)+(hi.astype(float)-lo.astype(float))*np.float32(row['phase'])).astype(np.uint8)
        opaque=(lo[:,:,3]>127)&(hi[:,:,3]>127)
        match=opaque & np.all(np.abs(actual.astype(np.int16)-expected.astype(np.int16))<=1,axis=2)
        if previous:
            prior,old_actual,old_expected,old_match=previous
            if row['identity'][:2]==prior['identity'][:2] and row['identity'][2]==prior['identity'][2]+1:
                transitions.append(dict(identity=row['identity'],**classify(old_actual,actual,old_expected,expected,old_match,opaque)))
        previous=row,actual,expected,match
    else:
        if rows:captures.append(dict(manifest=str(path),transitions=transitions))
assert captures
out=dict(result='POSSIBLE_STALE_SKY_PIXEL_DIAGNOSTIC',captures=captures,excluded=excluded,frozen_negative_control_detected=True,total_transitions=sum(len(c['transitions']) for c in captures),possible_stale_pixels=sum(t['possible_stale_pixels'] for c in captures for t in c['transitions']),scope='Eligibility uses prior agreement and current opaque source, never current agreement. Stale pixels may be foreground occlusion; no exclusive sky provenance, cadence or scanout verdict. Previous joint-match audit cannot independently reject frozen mismatching pixels.')
Path(sys.argv[1]).write_text(json.dumps(out,indent=2))
print({k:v for k,v in out.items() if k not in ('captures','excluded')})
