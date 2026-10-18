import sys,json,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());rows=r['presentation_samples'];owners=set();duration=[];late=[];intervals=[];previous=None
for row in rows:
 assert row['native_deadline_path'];owners.add(row['native_deadline_owner_thread'])
 if row['native_result']!=1:continue
 assert row['presentation']['status']==0
 stages=row['stages'];assert len(stages)==7 and stages==sorted(stages)
 t=row['callback_timing'];assert t['present_begin_ns']==stages[3] and t['present_end_ns']==stages[4]
 assert row['wait'][1]==row['presentation_deadline_ns']
 duration.append((stages[4]-stages[3])/1e6);late.append((stages[3]-row['presentation_deadline_ns'])/1e6)
 if previous is not None and (row['epoch'],row['generation'])==(previous['epoch'],previous['generation']) and row['display_index']==previous['display_index']+1:
  gap=(stages[4]-previous['stages'][4])/1e6;assert gap>=0;intervals.append(gap)
 previous=row
assert len(owners)==1 and duration
s=r['shutdown_evidence'];assert not s['gpu_thread_alive'] and not s['preparation_thread_alive'] and s['native_owner_released']
p=s['preparation_service_shutdown'];assert p['child_exitcode']==0 and not p['child_alive'] and not p['forced_termination']
def stats(v):
 v=sorted(v);return dict(count=len(v),median_ms=statistics.median(v),p95_ms=v[int(.95*(len(v)-1))],max_ms=max(v))
result=dict(result='PASS_NATIVE_DEADLINE_LIVE_TELEMETRY',owners=list(owners),native_present=stats(duration),deadline_lateness=stats(late),adjacent_native_present_intervals=stats(intervals),over25ms=sum(x>25 for x in intervals),over50ms=sum(x>50 for x in intervals),pause_events=len(r['pause_events']),scope='Native owner-thread API/commit wall times; no Python callback entered at deadline. Does not certify physical scanout, complete pixel fidelity or sustained60fps.')
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
