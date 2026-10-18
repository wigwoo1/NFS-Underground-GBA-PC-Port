import json,sys,statistics
from pathlib import Path
runs=[]
for filename in sys.argv[1:-1]:
 r=json.loads(Path(filename).read_text());jobs=[];allrows=[]
 for job in r['world_preparation_stage_samples']:
  t=job['terminal'][5];rows=t['sample_transfer_rows']
  if not rows:continue
  previous=t['constructed_ns'];parts=[]
  for index,row in enumerate(rows):
   assert row['index']==index and row['ready_ns']>=previous and row['prepare_since_ack_ns']==row['ready_ns']-previous
   assert all(row[k]>=0 for k in ('encode_ns','send_ns','ack_wait_ns'))
   sent=row['ready_ns']+row['encode_ns']+row['send_ns'];acked=sent+row['ack_wait_ns'];previous=acked
   part=dict(pair=[job['older'],job['newer']],generation=job['generation'],index=index,prepare_ms=row['prepare_since_ack_ns']/1e6,encode_ms=row['encode_ns']/1e6,send_ms=row['send_ns']/1e6,ack_ms=row['ack_wait_ns']/1e6,ready_ns=row['ready_ns'],acked_ns=acked)
   parts.append(part);allrows.append(part)
  assert previous<=t['child_finished_ns']
  jobs.append(dict(pair=[job['older'],job['newer']],samples=len(parts),first_ready_ms=(rows[0]['ready_ns']-t['constructed_ns'])/1e6,total_ack_ms=sum(x['ack_ms'] for x in parts),total_publication_ms=sum(x['encode_ms']+x['send_ms']+x['ack_ms'] for x in parts),post_last_ack_ms=(t['child_finished_ns']-previous)/1e6))
 assert allrows
 def summary(values):
  v=sorted(values);return dict(count=len(v),median=statistics.median(v),p95=v[int((len(v)-1)*.95)],maximum=v[-1],total=sum(v))
 stats={key:summary([x[key] for x in allrows]) for key in ('prepare_ms','encode_ms','send_ms','ack_ms')}
 runs.append(dict(source=filename,jobs=len(jobs),samples=len(allrows),summary_ms=stats,worst_ack=sorted(allrows,key=lambda x:x['ack_ms'],reverse=True)[:10],worst_first_ready=sorted(jobs,key=lambda x:x['first_ready_ms'],reverse=True)[:10],job_rows=jobs))
out=dict(result='PASS_EXACT_PUBLICATION_ACK_PARTITIONS',runs=runs,scope='Every retained sample-bearing job and every transfer row, exact constructed/ready/encoded/sent/ack chronology. First-ready precedes first send and ack, so that job first ack cannot cause its own first-ready delay. Later samples and subsequent job service may still be affected; no exclusive cause or live60 claim.')
Path(sys.argv[-1]).write_text(json.dumps(out,indent=2));print(json.dumps([dict(source=x['source'],jobs=x['jobs'],samples=x['samples'],summary_ms=x['summary_ms'],worst_ack=x['worst_ack'][:2]) for x in runs]))
