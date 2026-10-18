import sys,json,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows=[x for x in r['presentation_samples'] if x.get('native_result')==1];out={}
def stats(v):return dict(count=len(v),median_ms=statistics.median(v)/1e6,max_ms=max(v)/1e6)
for kind,key in [('prepare','prepared'),('present','presentation')]:
 values=[]
 for row in rows:
  d=row[key]['renderer_dispatch'];cb=row['callback_timing'];end=cb['draw_end_ns' if kind=='prepare' else 'present_end_ns'];assert d['submitted_ns']<=d['started_ns']<=d['completed_ns']<=end
  values.append(dict(queue=d['started_ns']-d['submitted_ns'],execution=d['completed_ns']-d['started_ns'],return_delay=end-d['completed_ns']))
 out[kind]={k:stats([x[k] for x in values]) for k in values[0]}
out['scope']='Retained120successful commands per kind, queue includes input polling/scheduling, execution contains native and Python work; return_delay contains publication/wakeup/GIL. No whole-run quantiles or causal CPU/GPU attribution.'
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
