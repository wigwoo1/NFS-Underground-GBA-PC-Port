import json,sys,statistics
from pathlib import Path
from analyze_producer_submission_join_candidate import joined
from analyze_slow_producer_gc_candidate import overlap

def analyze(r):
 audit=joined(r);out=[]
 for x in r['producer_retention']['long_scene_preparations']['records']:
  w=x['worker_submission'];a=w['handoff_allocate_ns'];c=w['handoff_memcpy_ns'];assert type(a) is int and type(c) is int and a>=0 and c>=0
  assert a+c<=w['native_copy_unlocked_ns']+200
  out.append(dict(refresh=x['refresh'],allocation_ms=a/1e6,memcpy_ms=c/1e6,copy_outer_ms=w['native_copy_unlocked_ns']/1e6,copy_other_ms=(w['native_copy_unlocked_ns']-a-c)/1e6,gc_overlap_ms=overlap(x['started_ns'],x['completed_ns'],r['gc_collection_samples'])/1e6))
 low=[x for x in out if x['gc_overlap_ms']<=2]
 return dict(result='COMPLETE_LIVE_HANDOFF_ALLOCATION_COPY_PARTITION',count=len(out),low_gc_count=len(low),low_gc_medians_ms={k:statistics.median(x[k] for x in low) for k in ('allocation_ms','memcpy_ms','copy_outer_ms','copy_other_ms')} if low else {},records=out,scope='Current-producer-thread TLS profile from same handoff DLL joined to exact scene submission; wall times include scheduling/cache effects, no exclusive CPU cause or gameplay60 proof.')
if __name__=='__main__':
 out=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print({k:v for k,v in out.items() if k!='records'})
