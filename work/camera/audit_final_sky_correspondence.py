"""Audit final committed sky correspondence without trusting saved match flags."""
import json,sys,hashlib
from pathlib import Path
rp,dp,op=map(Path,sys.argv[1:4]); r=json.loads(rp.read_text()); d=json.loads(dp.read_text())
committed={x['display_index']:x for x in r['presentation_samples'] if x.get('hidden_window_presented') and x.get('interpolated')}
rows=d['records']; transitions=[]; matches=total=stage_mismatches=stage_points=0
def near(a,b):return max(abs(v-w) for v,w in zip(a,b))<=1
for x in rows:
 assert 'error' not in x
 c=committed[x['display_index']]
 for k in ('epoch','source_older','refresh','alpha'): assert x[k]==c[k],k
 assert x['thread']==c['consumer_thread'] and x['selected_epoch']==c['epoch']
 for pt in x['sky_reference_points']:
  matches+=near(pt['actual'],pt['expected']); total+=1
  if 'stage' in pt:
   stage_points+=1; stage_mismatches+=not near(pt['stage'],pt['expected'])
assert stage_mismatches==0
for a,b in zip(rows,rows[1:]):
 if a['epoch']!=b['epoch'] or b['display_index']!=a['display_index']+1:continue
 both=changed=reference_changes=0
 for pa,pb in zip(a['sky_reference_points'],b['sky_reference_points']):
  assert (pa['x'],pa['y'])==(pb['x'],pb['y'])
  if near(pa['actual'],pa['expected']) and near(pb['actual'],pb['expected']):
   both+=1
   if pa['expected']!=pb['expected']:
    reference_changes+=1; changed+=pa['actual']!=pb['actual']
 transitions.append(dict(previous=a['display_index'],current=b['display_index'],both_matching_points=both,moving_reference_points=reference_changes,changed_final_points=changed,same_pair=(a['source_older'],a['refresh'])==(b['source_older'],b['refresh'])))
result=dict(result='AUDITED',images=len(rows),matched_final_points=matches,total_points=total,stage_points=stage_points,stage_mismatches=stage_mismatches if stage_points else None,stage_evidence='complete' if stage_points==total and total else ('partial' if stage_points else 'unavailable'),adjacent_transitions=len(transitions),matching_motion_transitions=sum(x['changed_final_points']>0 for x in transitions),same_pair_matching_motion_transitions=sum(x['same_pair'] and x['changed_final_points']>0 for x in transitions),transitions=transitions,input_hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (rp,dp)},scope='Archived selected full-scene target attributed to CPU commit identities. Color correspondence lacks independent visibility mask; synchronous readback perturbs timing. No physical scanout or sustained60fps proof.')
op.parent.mkdir(exist_ok=True);op.write_text(json.dumps(result,indent=2));(op.parent/Path(__file__).name).write_bytes(Path(__file__).read_bytes());print(json.dumps({k:v for k,v in result.items() if k not in ('transitions','input_hashes')},indent=2))


