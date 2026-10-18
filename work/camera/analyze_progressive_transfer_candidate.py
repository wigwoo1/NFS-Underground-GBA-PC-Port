from pathlib import Path
import json,sys,statistics
r=json.loads(Path(sys.argv[1]).read_text());rows=r['world_preparation_stage_samples'];assert rows and r['shutdown_evidence']['preparation_service_shutdown']['diagnostic_dropped']==0
child=[];parent=[];construct=[]
for row in rows:
 t=row['terminal'];assert t[2]=='complete' and t[3]==row['prepared_sample_count']
 d=t[5];c=d['sample_transfer_rows'];p=row['parent_sample_rows'];assert len(c)==len(p)==t[3]
 construct.append(d['constructed_ns']-d['child_started_ns'])
 for i,(a,b) in enumerate(zip(c,p)):
  assert a['index']==b['index']==i
  assert all(a[k]>=0 for k in ('encode_ns','send_ns','ack_wait_ns','prepare_since_ack_ns'))
  assert b['receive_begin_ns']<=b['received_ns']<=b['decoded_ns']<=b['publication_begin_ns']<=b['published_ns']<=b['ack_sent_ns']
  child.append(a);parent.append(b)
def summary(values):return dict(count=len(values),mean_ms=statistics.mean(values)/1e6,median_ms=statistics.median(values)/1e6,max_ms=max(values)/1e6,total_ms=sum(values)/1e6)
out=dict(result='PASS_PROGRESSIVE_TRANSFER_ACCOUNTING',requests=len(rows),samples=len(child),construct=summary(construct),child={k:summary([x[k] for x in child]) for k in ('prepare_since_ack_ns','encode_ns','send_ns','ack_wait_ns')},parent={name:summary([x[b]-x[a] for x in parent]) for name,a,b in [('receive','receive_begin_ns','received_ns'),('decode','received_ns','decoded_ns'),('publication','publication_begin_ns','published_ns'),('ack_send','published_ns','ack_sent_ns')]},scope='Elapsed synchronous stage ranges, including scheduling; parent and child overlap, do not sum across processes or infer exclusive CPU. First preparation range includes source setup.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
