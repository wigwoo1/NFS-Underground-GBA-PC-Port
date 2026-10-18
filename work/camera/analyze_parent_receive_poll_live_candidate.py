import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows=[]
for job in r['world_preparation_stage_samples']:
 child=job['terminal'][5]['sample_transfer_rows'];parent=job['parent_sample_rows'];assert len(child)==len(parent)
 for c,p in zip(child,parent):
  assert c['index']==p['index'];t=p['receive_poll'];q=p['shared_read'];w=c['shared_write'];assert t is not None
  stamps=[p['receive_begin_ns'],t['begin_ns'],t['poll_completed_ns'],t['recv_begin_ns'],q['begin_ns'],q['copied_ns'],q['decoded_ns'],t['received_ns'],p['received_ns'],p['decoded_ns'],p['published_ns']];assert stamps==sorted(stamps)
  assert w['payload_bytes']==q['payload_bytes'] and w['copied_ns']<=q['begin_ns']
  rows.append(dict(pair=[job['older'],job['newer']],index=c['index'],publication_to_poll_completion_ms=(t['poll_completed_ns']-w['copied_ns'])/1e6,poll_completion_to_recv_ms=(t['recv_begin_ns']-t['poll_completed_ns'])/1e6,recv_to_shared_reader_ms=(q['begin_ns']-t['recv_begin_ns'])/1e6,shared_copy_ms=(q['copied_ns']-q['begin_ns'])/1e6,pickle_decode_ms=(q['decoded_ns']-q['copied_ns'])/1e6,total_reader_start_delay_ms=(q['begin_ns']-w['copied_ns'])/1e6))
assert rows
summary={}
for key in rows[0]:
 if key.endswith('_ms'):
  v=sorted(x[key] for x in rows);summary[key]=dict(median=statistics.median(v),p95=v[int((len(v)-1)*.95)],maximum=v[-1])
intervals=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_intervals']
out=dict(result='PASS_LIVE_PARENT_POLL_SHARED_BOUNDARIES',samples=len(rows),summary_ms=summary,worst=sorted(rows,key=lambda x:x['total_reader_start_delay_ms'],reverse=True)[:10],native_intervals=intervals,scope='Actual live poll/receive/shared-copy chronology on every retained transfer. Poll completion includes notification and rescheduling, not exclusive OS or GIL cause; no full-scene physical60 claim.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='worst'}));print(out['worst'][:2])
