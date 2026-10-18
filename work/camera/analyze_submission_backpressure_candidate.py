"""Join complete long producer and submission-space records by identity/time."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text())
a=r['producer_retention']['long_scene_preparations']; b=r['submit_retention']['whole_submission_space_wait']
assert a['dropped']==0 and a['total']==len(a['records'])
assert b['dropped']==0 and b['long_total']==len(b['records'])
by={tuple(x['scene_identity']):x for x in b['records'] if not x['replay']}; matched=[]
for x in a['records']:
 candidates=[v for k,v in by.items() if k[1]==x['refresh'] and x['started_ns']<=v['submit_begin_ns']<=v['submit_end_ns']<=x['completed_ns']]
 assert len(candidates)<=1
 if not candidates:continue
 s=candidates[0]; wait=s['space_wait_ns']; total=x['ns']
 assert 0<=wait<=s['submit_end_ns']-s['submit_begin_ns']<=total
 matched.append(dict(refresh=x['refresh'],producer_ms=total/1e6,worker_submit_ms=x['stages']['worker_submit_ns']/1e6,queue_space_wait_ms=wait/1e6,other_submit_ms=(s['submit_end_ns']-s['submit_begin_ns']-wait)/1e6,wait_fraction=wait/total,preparation_submit_ms=s['preparation_submit_ns']/1e6))
assert matched
out=dict(result='PASS_COMPLETE_LONG_SUBMISSION_JOIN',complete_long_producers=a['total'],complete_long_space_waits=b['long_total'],matched_count=len(matched),whole_submission_space_wait_ms=b['total_ns']/1e6,largest=sorted(matched,key=lambda x:x['producer_ms'],reverse=True)[:20],scope='Complete retained long ledger join; queue capacity wait is backpressure, not exclusive GPU or preparation cause. No queue widening, source dropping or clock changes.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
