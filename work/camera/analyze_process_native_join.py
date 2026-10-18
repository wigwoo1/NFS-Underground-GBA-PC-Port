"""Analyze child frame join allocation/copy boundaries without CPU causality claims."""
import json,sys,statistics
from pathlib import Path

def analyze(report):
 rows=[]
 for job in report['world_preparation_stage_samples']:
  child=job['child_stages'];assert child['native_frame_join_enabled']
  for sample in child['sample_timings']:
   for stage in sample['assembly_stages']:
    if 'frame_join_trace' not in stage:continue
    t=stage['frame_join_trace'];a,b,f,c,d=t['native_boundary'];assert f>0 and a<=b and c<=d
    copy=(b-a)*1e9/f;call=t['native_call_ns'];assert copy<=call+100000
    rows.append(dict(source=[job['older'],job['newer']],alpha=sample['alpha'],bytes=t['bytes'],packing_ms=t['packing_ns']/1e6,allocation_ms=t['allocation_ns']/1e6,native_call_ms=call/1e6,native_copy_ms=copy/1e6,call_outside_copy_ms=(call-copy)/1e6,native_thread_cycles=d-c,encoding_stage_ms=stage['wall_ns']/1e6))
 assert rows
 return dict(samples=len(rows),native_copy_median_ms=statistics.median(x['native_copy_ms'] for x in rows),call_outside_copy_median_ms=statistics.median(x['call_outside_copy_ms'] for x in rows),largest=sorted(rows,key=lambda x:x['encoding_stage_ms'],reverse=True)[:20],scope='Native QPC copy elapsed versus Python call wall; outside-copy includes entry/exit and scheduling, not exclusive GIL proof. Encoding stage also includes model array construction.')
if __name__=='__main__':
 result=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
