import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows=[]
for job in r['world_preparation_stage_samples']:
 for p in job['parent_sample_rows']:
  q=p['shared_read'];d=q['descriptor_receive'];t=p['receive_poll'];assert d and t
  stamps=[t['recv_begin_ns'],d['begin_ns'],d['read_ns'],d['decoded_ns'],q['begin_ns'],q['copied_ns'],q['decoded_ns']];assert stamps==sorted(stamps)
  rows.append(dict(pair=[job['older'],job['newer']],index=p['index'],wire_bytes=d['wire_bytes'],wrapper_entry_ms=(d['begin_ns']-t['recv_begin_ns'])/1e6,pipe_read_ms=(d['read_ns']-d['begin_ns'])/1e6,descriptor_decode_ms=(d['decoded_ns']-d['read_ns'])/1e6,post_descriptor_ms=(q['begin_ns']-d['decoded_ns'])/1e6))
assert rows
summary={}
for key in rows[0]:
 if key.endswith('_ms'):
  v=sorted(x[key] for x in rows);summary[key]=dict(median=statistics.median(v),p95=v[int((len(v)-1)*.95)],maximum=v[-1])
out=dict(result='PASS_ACTUAL_DESCRIPTOR_READ_DECODE_BOUNDARIES',samples=len(rows),wire_sizes=sorted({x['wire_bytes'] for x in rows}),summary_ms=summary,worst_pipe_reads=sorted(rows,key=lambda x:x['pipe_read_ms'],reverse=True)[:10],native_intervals=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_intervals'],scope='Actual recv_bytes and pickle descriptor decode boundaries, matching sample identities; pipe-read wall duration includes blocking and post-native scheduling, not exclusive OS time or GIL cause.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='worst_pipe_reads'}));print(out['worst_pipe_reads'][:2])
