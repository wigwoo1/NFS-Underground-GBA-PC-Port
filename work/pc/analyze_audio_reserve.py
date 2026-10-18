from pathlib import Path
import csv,hashlib,json,statistics
out=Path('C:/NFSUG-Workspace/NFSUG-pc-audio-reserve-trace-tests');report=json.loads((out/'capture-report.json').read_text());trace=out/'reserve.csv';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(trace)==report['trace_sha256']
raw=list(csv.DictReader(trace.open()));assert len(raw)==12000
rows=[]
for r in raw:
 r={k:float(v) if k=='time' else int(v) for k,v in r.items()};rows.append(r)
for i in range(6000):
 before,after=rows[2*i:2*i+2];assert before['drain']==after['drain']==i+1 and before['phase']==0 and after['phase']==1
 assert after['time']>=before['time'] and after['produced']>=before['produced'] and after['submitted']>=before['submitted']
 assert after['submitted']+after['ring']==after['produced']
valid=[r for r in rows if r['started'] and r['result']==0 and r['type']==2 and r['played']<=r['submitted']]
pre=[r for r in valid if not r['phase']];post=[r for r in valid if r['phase']]
empty=[r for r in pre if r['queued']==0]
reserves=lambda rs:[(r['submitted']-r['played'])/44.1 for r in rs]
events=[];active=False
for r in pre:
 if r['queued']==0 and not active:
  i=r['drain'];previous=rows[2*(i-2)+1] if i>1 else None
  events.append(dict(drain=i,pre=r,previous_post=previous,pre_remaining_ms=(r['submitted']-r['played'])/44.1,previous_post_remaining_ms=(previous['submitted']-previous['played'])/44.1 if previous else None,between_drains_ms=1000*(r['time']-previous['time']) if previous else None))
 active=r['queued']==0
summary=lambda rs:dict(min_ms=min(reserves(rs)),median_ms=statistics.median(reserves(rs)),max_ms=max(reserves(rs)),below_16_667ms=sum(t<1000/60 for t in reserves(rs)),below_33_333ms=sum(t<1000/30 for t in reserves(rs)))
result=dict(result='VERIFIED_PAIRED_DRIVER_RESERVE_TRACE_ANALYSIS',rows=12000,valid_driver_rows=len(valid),pre_summary=summary(pre),post_summary=summary(post),empty_header_polls=len(empty),empty_header_events=events,host_empty_events=report['session']['audio_queue_empty_events'],trace_sha256=sha(trace),analysis_sha256=sha(Path(__file__)),production_changed=False,physical_audio_verified=False,limits='Read-only driver sample cursor may have driver-specific resolution/latency. Header flags and reported remaining samples are diagnostic signals, not proof of audible silence. Extra queries and CSV may perturb timing; cannot explain untraced prior events by assumption.')
result['trace_host_event_counts_equal']=len(events)==result['host_empty_events']
result['poll_boundary_note']='Trace query precedes the host flag poll; a driver completion between them can change event counts. Host also clears its empty-active flag after successful submission.'
(out/'analysis-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
