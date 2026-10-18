import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows=[]
for job in r['world_preparation_stage_samples']:
 child=job['terminal'][5]['sample_transfer_rows'];parent=job['parent_sample_rows']
 assert len(child)==len(parent)
 for c,p in zip(child,parent):
  assert c['index']==p['index'];sent=c['ready_ns']+c['encode_ns']+c['send_ns'];acked=sent+c['ack_wait_ns']
  stamps=[p['receive_begin_ns'],p['received_ns'],p['decoded_ns'],p['publication_begin_ns'],p['published_ns'],p['ack_sent_ns']]
  assert stamps==sorted(stamps) and p['published_ns']<=acked
  rows.append(dict(pair=[job['older'],job['newer']],index=c['index'],ack_ms=c['ack_wait_ns']/1e6,parent_receive_ms=(p['received_ns']-p['receive_begin_ns'])/1e6,parent_decode_ms=(p['decoded_ns']-p['received_ns'])/1e6,parent_before_publish_ms=(p['publication_begin_ns']-p['decoded_ns'])/1e6,parent_publish_ms=(p['published_ns']-p['publication_begin_ns'])/1e6,parent_ack_send_ms=(p['ack_sent_ns']-p['published_ns'])/1e6,ack_send_completion_to_child_receive_ms=(acked-p['ack_sent_ns'])/1e6))
assert rows
def summary(key):
 values=sorted(x[key] for x in rows);return dict(count=len(values),median=statistics.median(values),p95=values[int((len(values)-1)*.95)],maximum=values[-1])
out=dict(result='PASS_PARENT_CHILD_ACK_TIMELINE_JOIN',samples=len(rows),child_ack_before_parent_post_send_stamp=sum(x['ack_send_completion_to_child_receive_ms']<0 for x in rows),summary_ms={key:summary(key) for key in rows[0] if key.endswith('_ms')},worst_ack=sorted(rows,key=lambda x:x['ack_ms'],reverse=True)[:10],scope='Exact parent/child same-job sample index and monotonic QPC boundaries; receive spans waiting and decoding shared packet, not exclusive copy cost. Parent ack_sent is a post-send timestamp; child may receive before that stamp, retained signed interval is not a negative transport duration. Does not imply eliminating ack would safely preserve ownership.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out))
