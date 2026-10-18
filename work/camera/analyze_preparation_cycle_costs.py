"""Preparation wall/cycle comparison joined to actual active commit gaps."""
import json,sys,statistics
from pathlib import Path
from analyze_native_batch_gaps import analyze as gaps

def analyze(r):
 rows={x['display_index']:x for x in r['presentation_samples'] if 'display_index' in x}
 jobs=r['world_preparation_stage_samples'];bad=set();matched=[]
 for g in gaps(r)['largest']:
  row=rows[g['display_index']]
  candidates=[(i,j) for i,j in enumerate(jobs) if (j['older'],j['newer'])==tuple(g['source']) and j['completed_ns']<=row['pair_ready_ns']]
  if not candidates:continue
  i,j=max(candidates,key=lambda x:x[1]['completed_ns']);bad.add(i)
  matched.append(dict(display_index=g['display_index'],source=g['source'],gap_ms=g['gap_ms'],job_index=i,precompute_wall_ms=j['precompute_ns']/1e6,precompute_cycles=j['precompute_thread_cycles']))
 groups={}
 for i,j in enumerate(jobs):
  for sample in j.get('sample_timings',[]):
   for s in sample.get('assembly_stages',[]):
    assert s['wall_ns']>=0 and s['thread_cycles']>=0
    groups.setdefault((s['name'],'largest_gap_pairs' if i in bad else 'other_pairs'),[]).append(s)
 summary=[]
 for (name,group),ss in sorted(groups.items()):
  summary.append(dict(stage=name,group=group,count=len(ss),median_wall_ms=statistics.median(s['wall_ns'] for s in ss)/1e6,median_cycles=statistics.median(s['thread_cycles'] for s in ss),total_cycles=sum(s['thread_cycles'] for s in ss),maximum_wall_ms=max(s['wall_ns'] for s in ss)/1e6))
 return dict(result='VERIFIED_RECORDED_STAGE_COSTS',matched_gap_pairs=matched,stages=summary,scope='Exact latest-completed pair joins for largest 20 active gaps; other pairs can contain smaller gaps. Hardware thread cycles measure execution without converting to CPU time; wall includes scheduling and waits. Nested stages are not additive. No exclusive causal attribution or controlled performance comparison.')
if __name__=='__main__':
 out=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
