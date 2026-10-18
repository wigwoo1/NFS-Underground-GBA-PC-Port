"""Require complete long-scene ledger and exact native read/caller stage bounds."""
import json,sys,statistics
from pathlib import Path
from analyze_slow_producer_gc_candidate import overlap

def analyze(r):
 assert r['result']=='SMOKE_COMPLETE' and r['error'] is None and r['gc_trace_dropped']==0
 s=r['producer_retention']['long_scene_preparations'];assert s['dropped']==0 and s['total']==len(s['records'])
 assert r['producer_retention']['total_records']==r['timing']['producer_read_validate_reconstruct_submit']['count']
 out=[];seen=set()
 for x in s['records']:
  assert x['refresh'] not in seen;seen.add(x['refresh'])
  a=x['started_ns'];b=x['completed_ns'];assert a<=b and x['ns']*16777216>280896*1000000000
  stages=x['stages'];assert all(type(v) is int and v>=0 for v in stages.values())
  assert sum(stages.values())<=x['ns']
  reads=x['frame_read_boundaries']
  assert all(a<=z['started_ns']<=z['completed_ns']<=b for z in reads)
  out.append(dict(refresh=x['refresh'],wall_ms=(b-a)/1e6,total_measured_ms=x['ns']/1e6,stages_ms={k:v/1e6 for k,v in stages.items()},gc_overlap_ms=overlap(a,b,r['gc_collection_samples'])/1e6))
 low=[x for x in out if x['gc_overlap_ms']<=2]
 return dict(result='COMPLETE_LONG_SCENE_PREPARATION_PARTITION',count=len(out),low_gc_count=len(low),low_gc_stage_medians_ms={k:statistics.median(x['stages_ms'][k] for x in low) for k in low[0]['stages_ms']} if low else {},records=out,scope='Entire bounded long preparation ledger; stage medians not additive, GC correlation not exclusive causality, no pixel cadence proof.')
if __name__=='__main__':
 out=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='records'})
