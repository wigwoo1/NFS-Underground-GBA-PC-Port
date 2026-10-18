"""Compare a recorded refresh cluster without assuming identical scene inputs."""
import json,sys,statistics
from pathlib import Path
out={}
for name,path in zip(('baseline','candidate'),sys.argv[1:3]):
 r=json.loads(Path(path).read_text());lo,hi=9320,9450
 producers=[x for x in r['producer_cycle_samples'] if lo<=x['refresh']<=hi]
 updates=[x for x in r['original_update_samples'] if lo<=x['refresh']<=hi]
 preparations=[x for x in r['world_preparation_stage_samples'] if lo<=x['older']<=hi]
 lifecycle=[x for x in r['preparation_queue_samples'] if x.get('identity') is not None and lo<=x['identity'][1]<=hi and x.get('published_ns') is not None]
 durations=[x['ns']/1e6 for x in producers]
 out[name]=dict(producers=producers,updates=updates,preparations=preparations,lifecycle=lifecycle,summary=dict(producer_count=len(producers),producer_median_ms=statistics.median(durations),producer_max_ms=max(durations),update_max_ms=max((x['completed_ns']-x['started_ns'])/1e6 for x in updates),admission_lateness_max_ms=max((x['started_ns']-x['original_deadline_ns'])/1e6 for x in updates),preparation_max_ms=max((x['completed_ns']-x['started_ns'])/1e6 for x in preparations),queue_wait_max_ms=max((x['started_ns']-x['enqueued_ns'])/1e6 for x in lifecycle)),slowest_producers=sorted(producers,key=lambda x:x['ns'],reverse=True)[:5])
result=dict(runs=out,scope='Refresh9320..9450 original recorded timestamps; same refresh range only, not verified identical scene bytes/history. Wall timings include scheduling; no exclusive cause or physical scanout proof.')
Path(sys.argv[3]).write_text(json.dumps(result,indent=2));print({k:v['summary'] for k,v in out.items()});print({k:[(x['refresh'],round(x['ns']/1e6,3)) for x in v['slowest_producers']] for k,v in out.items()})

