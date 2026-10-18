"""Match recorded preparation jobs to actual consumed scene intervals."""
import json,sys,statistics
from pathlib import Path

def analyze(report):
 jobs=report['world_preparation_stage_samples'];rows=[];seen=set()
 for sample in report['presentation_samples']:
  if 'pair_begin_ns' not in sample:continue
  identity=(sample['source_older'],sample['refresh'],sample['pair_begin_ns'])
  if identity in seen:continue
  seen.add(identity)
  candidates=[job for job in jobs if job['older']==identity[0] and job['newer']==identity[1] and job['completed_ns']<=sample['pair_ready_ns']]
  if not candidates:continue
  job=max(candidates,key=lambda job:job['completed_ns'])
  rows.append(dict(older=identity[0],newer=identity[1],display_index=sample['display_index'],construct_ms=job['construct_advance_ns']/1e6,precompute_ms=job['precompute_ns']/1e6,construct_cpu_ms=job['construct_thread_cpu_ns']/1e6,precompute_cpu_ms=job['precompute_thread_cpu_ns']/1e6,preparation_completed_after_deadline_ms=max(0,job['completed_ns']-sample['presentation_deadline_ns'])/1e6,pair_wait_ms=sample['pair_prepare_ns']/1e6,preparation_overlap_pair_wait_ms=max(0,min(job['completed_ns'],sample['pair_ready_ns'])-max(job['started_ns'],sample['pair_begin_ns']))/1e6))
 def summary(key):
  values=[r[key] for r in rows]
  return dict(median=statistics.median(values),p95=sorted(values)[int(.95*(len(values)-1))],max=max(values)) if values else None
 return dict(scope='Actual preparation interval matched by source pair and completion before pair-ready; inclusive wall times and coarse CPU, overlap not causal or additive proof; repeated pause jobs may share identities.',matched_pairs=len(rows),late_prepared_pairs=sum(r['preparation_completed_after_deadline_ms']>0 for r in rows),summary={k:summary(k) for k in ['construct_ms','precompute_ms','construct_cpu_ms','precompute_cpu_ms','preparation_completed_after_deadline_ms','pair_wait_ms']},worst=sorted(rows,key=lambda r:r['pair_wait_ms'],reverse=True)[:12],pairs=rows)
if __name__=='__main__':
 p=Path(sys.argv[1]);result=analyze(json.loads(p.read_text()));p.with_suffix('.preparation-readiness.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ('worst','pairs')},indent=2))
