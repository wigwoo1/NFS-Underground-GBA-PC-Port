import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows=[]
for job in r['world_preparation_stage_samples']:
 children=job['terminal'][5]['sample_transfer_rows'];parents=job['parent_sample_rows'];assert len(children)==len(parents)
 for i,(c,p) in enumerate(zip(children,parents)):
  assert c['index']==p['index']==i
  w=c['shared_write'];q=p['shared_read'];assert p['receive_begin_ns']<=q['begin_ns'] and w['copied_ns']<=q['begin_ns']
  if i:assert parents[i-1]['published_ns']<=p['receive_begin_ns']
  rows.append(dict(pair=[job['older'],job['newer']],index=i,reader_delay_ms=(q['begin_ns']-w['copied_ns'])/1e6,parent_already_in_receive=p['receive_begin_ns']<=w['copied_ns'],parent_receive_entry_minus_publication_ms=(p['receive_begin_ns']-w['copied_ns'])/1e6,after_previous_ack_to_receive_entry_ms=None if i==0 else (p['receive_begin_ns']-parents[i-1]['ack_sent_ns'])/1e6))
slow=[x for x in rows if x['reader_delay_ms']>2]
out=dict(result='PASS_PARENT_RECEIVE_WAIT_STATE',samples=len(rows),already_in_receive=sum(x['parent_already_in_receive'] for x in rows),reader_delay_over2ms=len(slow),slow_already_in_receive=sum(x['parent_already_in_receive'] for x in slow),worst=sorted(rows,key=lambda x:x['reader_delay_ms'],reverse=True)[:10],scope='Receive entry before shared publication proves parent entered its poll/receive wrapper, not OS blocking or runnable state. Separate poll completion/recv entry stamps required for notification versus thread scheduling attribution.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out))
