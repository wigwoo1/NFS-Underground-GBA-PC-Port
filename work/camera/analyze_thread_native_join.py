"""Verify native frame-copy boundaries from actual threaded preparation."""
import json,sys,statistics
from pathlib import Path

def analyze(r):
 assert r['thread_native_frame_join_enabled'] and not r['process_preparation_enabled']
 rows=[]
 for j in r['world_preparation_stage_samples']:
  for sample in j.get('sample_timings',[]):
   for stage in sample['assembly_stages']:
    if stage['name']!='immutable_frame_join':continue
    t=stage['frame_join_trace'];a,b,f,c,d=t['native_boundary']
    assert f>0 and a<=b and c<=d and t['bytes']==stage['frame_bytes']
    assert stage['geometry_bytes']+stage['tail_bytes']+40==t['bytes']
    rows.append(dict(bytes=t['bytes'],copy_ms=(b-a)*1000/f,packing_ms=t['packing_ns']/1e6,allocation_ms=t['allocation_ns']/1e6,outer_ms=stage['wall_ns']/1e6,copy_cycles=d-c))
 assert rows
 return dict(result='PASS_THREADED_NATIVE_COPY_BOUNDARIES',samples=len(rows),median={k:statistics.median(x[k] for x in rows) for k in rows[0]},largest=sorted(rows,key=lambda x:x['outer_ms'],reverse=True)[:10],scope='Actual synchronous threaded native-copy QPC and byte-size boundaries; copy cycles are not instructions; no physical scanout or exclusive scheduling attribution.')
if __name__=='__main__':
 out=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out['median']))
