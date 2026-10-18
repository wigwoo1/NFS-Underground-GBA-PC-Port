"""Audit actual committed native presentation indices across source-scene replay."""
import json,sys
from pathlib import Path
from collections import Counter

def verify(report):
 samples=[row['native_committed_sample'] for row in report['presentation_samples'] if row.get('native_committed_sample')]
 assert samples and report['pause_events']
 indices=[int(x[4]) for x in samples];counts=Counter(indices)
 assert all(b==a+1 for a,b in zip(indices,indices[1:])), 'Native presentation index skipped/repeated'
 checks=[]
 for event in report['pause_events']:
  planned=event['buffer_at_begin']['planned_replay_indices'];last=event['buffer_at_begin']['last_committed']['display_index']
  if planned:
   if event['buffer_at_begin'].get('initial_replay'):
    assert last is None and not any(x[6]<event['native_pause_ack_ns'] for x in samples), 'Initial replay after an actual interpolated commit'
    assert planned[0]==indices[0], 'Initial replay skipped first presentation'
   else:assert planned[0]==last+1
   assert planned==list(range(planned[0],planned[-1]+1))
  else:
   buffer=event['buffer_at_begin']
   assert buffer['last_submitted_refresh']==buffer['last_committed']['refresh'], 'Empty replay despite uncommitted source'
   assert not buffer['snapshot_refreshes'] and not buffer['prepared_intervals'], 'Empty replay despite pending ownership'
  republished=event['republished_refreshes'];assert len(republished)>=2 and all(b>a for a,b in zip(republished,republished[1:]))
  pending=[x for x in samples if x[4] in planned]
  assert [x[4] for x in pending]==planned and all(counts[i]==1 for i in planned), 'Pending replay presentations lost/repeated'
  assert all(x[6]>=event['native_resume_ack_ns'] for x in pending), 'Pending replay committed before resume acknowledgment'
  assert all(x[2] in republished and x[3] in republished for x in pending), 'Replay source interval escaped republished scene chain'
  checks.append(dict(planned=planned,exactly_once=True,empty_replay_verified=not planned,source_refreshes=republished))
 return dict(result='PASS_EXACT_PENDING_REPLAY_COMMITS',native_commits=len(samples),pauses=checks,scope='Actual native committed sample identities/indices/ack timestamps; no physical scanout or full motion fidelity proof')
if __name__=='__main__':
 r=json.loads(Path(sys.argv[1]).read_text());out=verify(r);Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
