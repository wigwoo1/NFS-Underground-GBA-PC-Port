"""Join asynchronous GPU query identities to original native presentation rows."""
import json,sys,statistics
from pathlib import Path
def analyze(report):
 rows=[x for x in report['presentation_samples'] if x.get('native_batch_candidate')]
 origins={};completed={}
 for x in rows:
  q=x['gpu_timestamp_probe'];assert x['gpu_timestamp_result']==0 and q[0]==1 and q[6]==0
  identity=q[7];assert identity not in origins;origins[identity]=x
  assert x['gpu_fence_probe'][6]==0
  for k in range(q[2]):
   a=q[8+k*6:14+k*6];assert len(a)==6 and a[0] not in completed and a[1]<=a[2]<=a[3]<=a[4]
   completed[a[0]]=a
 joins=[];unmapped=[]
 for identity,a in completed.items():
  if identity not in origins:unmapped.append(identity);continue
  x=origins[identity];joins.append(dict(sequence=identity,display_index=x['display_index'],gpu_draw_ms=(a[2]-a[1])/1e6,gpu_draw_to_blit_ms=(a[3]-a[2])/1e6,gpu_window_blit_ms=(a[4]-a[3])/1e6,cpu_draw_ms=x['draw_cpu_ns']/1e6,present_stages_ms=[v/1e6 for v in x['native_present_stage_ns']],fence=x['gpu_fence_probe']))
 swaps=sorted(joins,key=lambda x:x['present_stages_ms'][1],reverse=True)
 return dict(result='PASS_QUERY_IDENTITY_JOINS',presentations=len(rows),gpu_records=len(completed),joined=len(joins),unmapped_query_sequences=unmapped,pending_final=rows[-1]['gpu_timestamp_probe'][1],diagnostic_skipped_final=rows[-1]['gpu_timestamp_probe'][3],median_gpu_draw_ms=statistics.median(x['gpu_draw_ms'] for x in joins),median_window_blit_ms=statistics.median(x['gpu_window_blit_ms'] for x in joins),worst_swaps=swaps[:5],joins=joins,scope='Available-only GPU timestamp differences; GPU ranges may contain idle submission time, GPU/QPC clock origins not subtracted; fences are polled at timeout0. No physical scanout proof.')
if __name__=='__main__':
 out=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='joins'},indent=2))
