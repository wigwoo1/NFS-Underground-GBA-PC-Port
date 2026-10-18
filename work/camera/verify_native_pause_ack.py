import sys,json
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());commits=[]
for row in r['presentation_samples']:
 if row.get('native_committed_sample'):commits.append(row['native_committed_sample'])
assert commits and r['pause_events']
checks=[]
for event in r['pause_events']:
 begin=event['native_pause_ack_ns'];end=event['native_resume_ack_ns']
 assert event['begin_ns']<=begin<end and event['end_ns']<=end
 assert event['native_pause_lock_wait_ns']>=0 and event['native_resume_lock_wait_ns']>=0
 violations=[sample for sample in commits if begin<=sample[6]<end]
 assert not violations,'Native presentation committed after pause acknowledgment'
 checks.append(dict(native_pause_ack_ns=begin,native_resume_ack_ns=end,commits_while_native_paused=len(violations),pause_lock_wait_ms=event['native_pause_lock_wait_ns']/1e6,resume_lock_wait_ms=event['native_resume_lock_wait_ns']/1e6,request_to_ack_ms=(begin-event['begin_ns'])/1e6))
out=dict(result='PASS_NATIVE_PAUSE_ACK',commits_checked=len(commits),pauses=checks,scope='Native committed sample timestamps versus acknowledged paused interval; game requested pause clock preserved; no physical scanout/controller claim')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
