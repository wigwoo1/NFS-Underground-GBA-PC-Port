from pathlib import Path
import json,sys
r=json.loads(Path(sys.argv[1]).read_text());assert r['gc_trace_dropped']==0
rows=[]
for request in r['world_preparation_stage_samples']:
 c=request['terminal'][5]['sample_transfer_rows'];p=request['parent_sample_rows'];assert len(c)==len(p)==request['prepared_sample_count']
 for child,parent in zip(c,p):
  assert child['index']==parent['index']
  a=child['ready_ns']+child['encode_ns'];b=a+child['send_ns'];ack=b+child['ack_wait_ns'];gc=[]
  for event in r['gc_collection_samples']:
   overlap=max(0,min(b,event['end_ns'])-max(a,event['start_ns']))
   if overlap:gc.append(dict(thread_id=event['thread_id'],generation=event['generation'],overlap_ms=overlap/1e6))
  rows.append(dict(older=request['older'],newer=request['newer'],index=child['index'],send_ms=child['send_ns']/1e6,parent_received_before_child_send_return=parent['received_ns']<b,parent_ack_before_child_send_return=parent['ack_sent_ns']<b,after_parent_ack_ms=max(0,b-parent['ack_sent_ns'])/1e6,parent_gc_overlap=gc))
out=dict(result='PASS_PROGRESSIVE_SCHEDULING_ORDER_ACCOUNTING',samples=len(rows),ack_before_send_return=sum(x['parent_ack_before_child_send_return'] for x in rows),receive_before_send_return=sum(x['parent_received_before_child_send_return'] for x in rows),longest=sorted(rows,key=lambda x:x['send_ms'],reverse=True)[:12],scope='Same-host monotonic timestamp ordering; acknowledgement before send return proves elapsed send includes post-publication delay, not its exclusive scheduling cause. GC overlap is correlation only; no child GC trace present.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result']);print('Samples',out['samples'],'ack before send return',out['ack_before_send_return'])
for x in out['longest'][:3]:print(x)
