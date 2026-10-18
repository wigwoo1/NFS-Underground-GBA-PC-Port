from pathlib import Path
import json,statistics,sys
r=json.loads(Path(sys.argv[1]).read_text());rows=[];values={}
for request in r['world_preparation_stage_samples']:
 child=request['terminal'][5]['sample_transfer_rows'];parent=request['parent_sample_rows'];assert len(child)==len(parent)==request['prepared_sample_count']
 for a,b in zip(child,parent):
  w=a['shared_write'];q=b['shared_read'];assert w and q and w['payload_bytes']==q['payload_bytes']
  assert w['begin_ns']<=w['serialized_ns']<=w['copied_ns']<=w['descriptor_sent_ns'];assert q['begin_ns']<=q['copied_ns']<=q['decoded_ns']
  phases=dict(serialize_ns=w['serialized_ns']-w['begin_ns'],shared_copy_ns=w['copied_ns']-w['serialized_ns'],descriptor_send_ns=w['descriptor_sent_ns']-w['copied_ns'],private_copy_ns=q['copied_ns']-q['begin_ns'],unpickle_ns=q['decoded_ns']-q['copied_ns'])
  for k,v in phases.items():values.setdefault(k,[]).append(v)
  rows.append(dict(older=request['older'],newer=request['newer'],index=a['index'],payload_bytes=w['payload_bytes'],phases_ms={k:v/1e6 for k,v in phases.items()},parent_copied_before_descriptor_return=q['copied_ns']<w['descriptor_sent_ns']))
out=dict(result='PASS_COMPLETE_SHARED_PHASE_ACCOUNTING',samples=len(rows),payload_min=min(x['payload_bytes'] for x in rows),payload_max=max(x['payload_bytes'] for x in rows),summary={k:dict(mean_ms=statistics.mean(v)/1e6,max_ms=max(v)/1e6) for k,v in values.items()},slowest=sorted(rows,key=lambda x:sum(x['phases_ms'].values()),reverse=True)[:8],scope='Elapsed synchronous stage boundaries include scheduling and overlap across processes; no exclusive CPU or visible60 claim.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out['result']);print(out['summary']);print('Payload bytes',out['payload_min'],out['payload_max'])
