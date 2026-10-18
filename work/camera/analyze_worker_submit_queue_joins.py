"""Exact slow source submission identity joins to bounded queue-wait ledger."""
import json,sys
from pathlib import Path
d=json.loads(Path(sys.argv[1]).read_text());q=d['submit_retention']['whole_submission_space_wait'];s=d['producer_retention']['long_scene_preparations'];assert q['dropped']==0 and q['long_total']==len(q['records']) and s['dropped']==0 and s['total']==len(s['records'])
rows=[]
for refresh in [12803,12627]:
 producers=[x for x in s['records'] if x['refresh']==refresh];assert len(producers)==1;p=producers[0]
 matches=[x for x in q['records'] if x['scene_identity'][1]==refresh and p['started_ns']<=x['submit_begin_ns']<=x['submit_end_ns']<=p['completed_ns']];assert len(matches)==1;x=matches[0]
 assert x['space_wait_ns']<=x['submit_end_ns']-x['submit_begin_ns']
 rows.append(dict(refresh=refresh,scene_identity=x['scene_identity'],producer_ms=p['ns']/1e6,worker_submit_ms=p['stages']['worker_submit_ns']/1e6,queue_space_wait_ms=x['space_wait_ns']/1e6,frame_ownership_ms=x['frame_ownership_ns']/1e6,snapshot_lock_ms=x['snapshot_lock_ns']/1e6,preparation_submit_ms=x['preparation_submit_ns']/1e6,queue_fraction=x['space_wait_ns']/p['stages']['worker_submit_ns']))
out=dict(result='PASS_EXACT_WORKER_SUBMIT_QUEUE_JOINS',queue_long_count=q['long_total'],queue_wait_total_ms=q['total_ns']/1e6,queue_wait_max_ms=q['max_ns']/1e6,rows=rows,scope='Two exact source identity/time joins; queue-space admission elapsed dominates submission. Does not identify why consumer capacity is unavailable or prove exclusive cause/60fps.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out))
