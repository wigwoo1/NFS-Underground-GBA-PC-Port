"""Separate broad encoding label from observed per-sample byte conversion."""
import json,sys
from pathlib import Path

def analyze(report):
 rows=[]
 for job in report['world_preparation_stage_samples']:
  child=job['child_stages'];b=child['child_boundaries'];trace=child['encode_samples']
  if not trace:continue
  assert b['sampled_ns']<=trace[0]['started_ns']
  assert trace[-1]['completed_ns']<=b['encoded_ns']
  for a,c in zip(trace,trace[1:]):assert a['completed_ns']<=c['started_ns']
  measured=sum(x['completed_ns']-x['started_ns'] for x in trace)
  broad=b['encoded_ns']-b['sampled_ns']
  rows.append(dict(source=[job['older'],job['newer']],broad_encoding_ms=broad/1e6,before_sample_encoding_ms=(trace[0]['started_ns']-b['sampled_ns'])/1e6,sample_encoding_ms=measured/1e6,after_sample_encoding_ms=(b['encoded_ns']-trace[-1]['completed_ns'])/1e6,between_samples_ms=(trace[-1]['completed_ns']-trace[0]['started_ns']-measured)/1e6,sample_thread_cycles=sum(x['thread_cycles'] for x in trace),child_total_cpu_ms=child['child_thread_cpu_ns']/1e6))
 return dict(jobs=len(rows),largest=sorted(rows,key=lambda x:x['broad_encoding_ms'],reverse=True)[:20],scope='Existing monotonic wall boundaries; broad encoding includes samples.close, previous-scene replacement and scheduling. Child total CPU covers whole job, not encoding alone. GC unobserved.')
if __name__=='__main__':
 result=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps(result['largest'][:3],indent=2))
