"""Compare draw wall time and executed cycles without treating wall time as CPU time."""
import json, statistics, sys
from pathlib import Path

def analyze(report):
 rows=[r for r in report['presentation_samples'] if r.get('native_draw_boundary')]
 assert rows
 valid=[]
 for r in rows:
  start,end,cycles,_=r['native_draw_boundary']
  assert end>=start and cycles>=0
  if cycles==(1<<64)-1 or end==start:continue
  valid.append((r,(end-start)/1e6,cycles))
 reference=statistics.median(c/w for _,w,c in valid if w<5)
 result=[]
 for row,wall,cycles in sorted(valid,key=lambda x:x[1],reverse=True)[:16]:
  result.append(dict(display_index=row['display_index'],wall_ms=wall,executed_cycles=cycles,cycles_per_wall_ms=cycles/wall,relative_to_short_draw_median=(cycles/wall)/reference,pair_acquisition_ms=row['pair_prepare_ns']/1e6,batch_owner_stage=row.get('batch_owner_stage')))
 return dict(result='ANALYZED',draws=len(valid),short_draw_median_cycles_per_ms=reference,largest=result,scope='Thread execution cycles versus elapsed draw callback time. Low density can reflect descheduling, driver waits or frequency changes; cannot establish exclusive cause or convert cycles to CPU milliseconds. draw_cpu_ns in the source report is elapsed wall time despite its name.')
if __name__=='__main__':
 rp,out=map(Path,sys.argv[1:3]);data=analyze(json.loads(rp.read_text()));out.write_text(json.dumps(data,indent=2));print(json.dumps(data,indent=2))
