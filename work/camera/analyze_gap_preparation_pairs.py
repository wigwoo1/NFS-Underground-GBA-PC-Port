"""Join native gaps to exact source preparation pairs, without causal inference."""
import json,sys
from pathlib import Path
from analyze_batch_gc_gaps import analyze as gap_audit

def analyze(report):
 result=gap_audit(report)
 jobs={}
 for job in report['world_preparation_stage_samples']:
  jobs.setdefault((job['older'],job['newer']),[]).append(job)
 rows={x['display_index']:x for x in report['presentation_samples'] if 'display_index' in x}
 for gap in result['largest']:
  row=rows[gap['display_index']]
  # Replay can prepare the same pair more than once; select the latest completed
  # preparation that existed when this consumer acquired its pair.
  candidates=[j for j in jobs.get(tuple(gap['source']),[]) if j['completed_ns']<=row['pair_ready_ns']]
  if not candidates:
   gap['preparation_match']='missing';continue
  job=max(candidates,key=lambda j:j['completed_ns'])
  assert job['started_ns']<=job['constructed_ns']<=job['completed_ns']
  stages=job.get('construct_stages',[])
  sample_rows=[]
  totals={}
  for sample in job.get('sample_timings',[]):
   parts=[]
   for part in sample.get('assembly_stages',[]):
    assert part['started_ns']<=part['completed_ns']
    value=part['wall_ns']/1e6
    totals[part['name']]=totals.get(part['name'],0)+value
    parts.append(dict(name=part['name'],wall_ms=value))
   sample_rows.append(dict(alpha=sample['alpha'],wall_ms=sample['wall_ns']/1e6,stages=parts))
  gap['preparation_samples']=sample_rows
  gap['assembly_stage_totals_ms']=totals
  gap['preparation']=dict(older=job['older'],newer=job['newer'],sample_count=job['prepared_sample_count'],construct_ms=(job['constructed_ns']-job['started_ns'])/1e6,precompute_ms=(job['completed_ns']-job['constructed_ns'])/1e6,ready_to_acquire_ms=(row['pair_ready_ns']-job['completed_ns'])/1e6,largest_construct_stages=sorted([dict(name=x['name'],wall_ms=x['wall_ns']/1e6) for x in stages],key=lambda x:x['wall_ms'],reverse=True)[:4])
 result['scope']+=' Exact refresh pair join chooses latest completed job before acquisition; nested stages overlap and are not additive. No OS scheduling or GPU causal attribution.'
 return result
if __name__=='__main__':
 a=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(a,indent=2));print(json.dumps(a,indent=2))
