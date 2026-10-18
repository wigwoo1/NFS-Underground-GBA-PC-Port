"""Join asynchronously retired GPU timestamp sequences to native presentation rows."""
import json,sys
from pathlib import Path

def analyze(report):
 rows=[x for x in report['presentation_samples'] if x.get('native_batch_candidate')];assert rows
 records={};sources={};retired=0;prior=0
 for x in rows:
  q=x['gpu_timestamp_probe'];assert len(q)==104 and x['gpu_timestamp_result']==0 and q[0]==1 and q[6]==0
  assert 0<=q[1]<=16 and 0<=q[2]<=16 and q[7]==q[4] and q[4]>prior
  assert q[1]+q[3]+q[5]==q[4];prior=q[4];sources[q[7]]=x
  for i in range(q[2]):
   z=q[8+i*6:14+i*6];assert z[0] not in records and z[0]<=q[7]
   assert 0<z[1]<=z[2]<=z[3]<=z[4] and z[5]>0
   records[z[0]]=z;retired+=1
  assert q[5]==retired
 assert records and report['shutdown_evidence']['gpu_queries_after_close']==0
 joined=[]
 for seq,z in records.items():
  assert seq in sources
  x=sources[seq]
  joined.append(dict(sequence=seq,display_index=x['display_index'],gpu_draw_range_ms=(z[2]-z[1])/1e6,gpu_blit_range_ms=(z[4]-z[3])/1e6,gpu_between_draw_blit_ms=(z[3]-z[2])/1e6,native_swap_ms=x['native_present_stage_ns'][1]/1e6,native_swap_thread_cycles=x['native_present_thread_cycles'][1],observed_cpu_ns=z[5]))
 return dict(result='PASS_ASYNC_GPU_TIMESTAMP_IDENTITIES',samples=len(rows),retired_records=len(records),diagnostic_skipped=rows[-1]['gpu_timestamp_probe'][3],pending_at_last_sample=rows[-1]['gpu_timestamp_probe'][1],worst_swap=sorted(joined,key=lambda x:x['native_swap_ms'],reverse=True)[:20],largest_draw_ranges=sorted(joined,key=lambda x:x['gpu_draw_range_ms'],reverse=True)[:12],scope='GPU command-stream timestamp ranges, asynchronously read only after availability checks. Ranges can include preemption/submission gaps; CPU/GPU clocks have different origins and are never directly compared. No physical scanout or consistent gameplay proof.')

if __name__=='__main__':
 result=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
