"""Observed preparation cleanup and GC overlap; no causal claim from wall time."""
import json,sys
from pathlib import Path

def analyze(report):
 rows=[];collections=0;dropped=0
 for job in report['world_preparation_stage_samples']:
  child=job['child_stages'];assert child['child_gc_observed'] is True
  gc=child['child_gc_rows'];collections+=len(gc);dropped=max(dropped,child['child_gc_dropped'])
  for x in gc:assert x['start_ns']<=x['end_ns'] and x['thread_cpu_ns']>=0
  c=child['encoding_cleanup']
  if c is None:continue
  assert c['close_begin_ns']<=c['close_end_ns']<=c['replacement_begin_ns']<=c['replacement_end_ns']
  for stage in ('close','replacement'):
   a,b=c[stage+'_begin_ns'],c[stage+'_end_ns'];cpu=c[stage+'_cpu_ns'];assert cpu>=0
   overlaps=[dict(generation=x['generation'],wall_overlap_ms=max(0,min(b,x['end_ns'])-max(a,x['start_ns']))/1e6,collection_cpu_ms=x['thread_cpu_ns']/1e6) for x in gc if x['start_ns']<b and x['end_ns']>a]
   rows.append(dict(source=[job['older'],job['newer']],stage=stage,wall_ms=(b-a)/1e6,cpu_ms=cpu/1e6,thread_cycles=c.get(stage+'_thread_cycles'),gc_overlaps=overlaps))
 return dict(stages=len(rows),collections=collections,dropped=dropped,largest=sorted(rows,key=lambda x:x['wall_ms'],reverse=True)[:20],scope='Child GC observer active; bounded dropped count governs coverage. Thread CPU timer may have coarse resolution; zero CPU does not prove zero work. Overlap is not exclusive causality.')
if __name__=='__main__':
 result=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
