"""Separate actual sky-layer readbacks from later fullscene coverage."""
import json,sys
from pathlib import Path
capture=Path(sys.argv[1]);report=Path(sys.argv[2]);out=Path(sys.argv[3])
a=json.loads(capture.read_text());r=json.loads(report.read_text());assert not a['errors'] and a['captures']
lookup={x['sample_begin_ns']:x for x in r['presentation_samples'] if x.get('native_committed_sample')}
maximum=covered=total=expected_moves=background_moves=visible_moves=visible_changed=0;prev=None
for c in a['captures']:
 row=lookup[c['draw_started_ns']];assert row['sky_fraction']==c['weight']
 final=bytes.fromhex(c['actual']);bg=bytes.fromhex(c['background']);expected=bytes.fromhex(c['expected']);assert len(final)==len(bg)==len(expected)==720
 for i in range(0,720,3):
  error=max(abs(bg[i+k]-expected[i+k]) for k in range(3));maximum=max(maximum,error);assert error<=1
  total+=1;covered+=final[i:i+3]!=bg[i:i+3]
  if prev:
   pf,pb,pe,pr=prev
   if row['epoch']==pr['epoch'] and row['display_index']==pr['display_index']+1 and max(abs(expected[i+k]-pe[i+k]) for k in range(3))>=4:
    expected_moves+=1;background_moves+=bg[i:i+3]!=pb[i:i+3]
    if final[i:i+3]==bg[i:i+3] and pf[i:i+3]==pb[i:i+3]:
     visible_moves+=1;visible_changed+=final[i:i+3]!=pf[i:i+3]
 prev=(final,bg,expected,row)
assert expected_moves and background_moves==expected_moves and visible_changed==visible_moves
result=dict(result='PASS_LIVE_SKY_LAYER_AND_COVERAGE',captures=len(a['captures']),sampled_centers=total,max_background_reference_channel_error=maximum,centers_changed_by_foreground=covered,strong_expected_changes=expected_moves,actual_background_changes=background_moves,uncovered_strong_expected_changes=visible_moves,actual_uncovered_changes=visible_changed,scope='Actual live selected target before geometry/HUD and after complete drawing, row44 at240pixelcenters, joined to native committed timestamps and weights. Foreground differences measured directly. Limited row/short steering run; no whole-sky fidelity or physical scanout/smoothness claim; two readbacks and callback add overhead.')
out.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
