from pathlib import Path
import csv,hashlib,json,statistics
out=Path('C:/NFSUG-Workspace/NFSUG-pc-existing-audio-query-tests');report=json.loads((out/'capture-report.json').read_text());s=report['session'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(out/'existing-query.csv')==report['trace_sha256']
rows=[{k:float(v) if k=='time' else int(v) for k,v in r.items()} for r in csv.DictReader((out/'existing-query.csv').open())]
pre=[r for r in rows if r['phase']==0];post=[r for r in rows if r['phase']==2];queries=[r for r in rows if r['phase']==1];events=[r for r in rows if r['phase']==3]
assert len(pre)==len(post)==6000 and len(queries)==s['audio_duration_queries'] and len(events)==s['audio_queue_empty_events']
assert len(rows)==12000+len(queries)+len(events)
for i,(a,b) in enumerate(zip(pre,post),1):
 assert a['drain']==b['drain']==i and b['time']>=a['time'] and b['submitted']+b['ring']==b['produced']
assert all(rows[i]['time']<=rows[i+1]['time'] for i in range(len(rows)-1))
for r in queries:
 if r['valid']:assert r['result']==0 and r['type']==2 and r['remaining']==r['submitted']-r['played']
assert sum(r['valid'] for r in queries)==s['audio_duration_valid']
contexts=[]
for e in events:
 prior=[q for q in queries if q['time']<e['time'] and q['valid']]
 q=prior[-1] if prior else None
 contexts.append(dict(event=e,previous_query=q,age_ms=1000*(e['time']-q['time']) if q else None,ideal_projected_reserve_frames=q['remaining']+e['submitted']-q['submitted']-(e['time']-q['time'])*44100 if q else None))
valid=[q for q in queries if q['valid']]
anchor=valid[0];period=280896/16777216
late=lambda q:1000*((q['time']-anchor['time'])-(q['drain']-anchor['drain'])*period)
lowest=min(valid,key=lambda q:q['remaining'])
service_gaps=sorted([dict(drain=b['drain'],gap_ms=1000*(b['time']-a['time'])) for a,b in zip(pre,pre[1:])],key=lambda r:r['gap_ms'],reverse=True)[:5]
result=dict(result='VERIFIED_EXISTING_QUERY_TRACE_COUNTS_AND_CONSERVATION',rows=len(rows),driver_query_rows=len(queries),host_driver_queries=s['audio_duration_queries'],event_contexts=contexts,empty_events=len(events),valid_reserve_min_ms=min(q['remaining'] for q in valid)/44.1,valid_reserve_median_ms=statistics.median(q['remaining'] for q in valid)/44.1,trace_sha256=report['trace_sha256'],analysis_sha256=sha(Path(__file__)),additional_driver_queries=0,file_writes_during_playback=0,production_changed=False,physical_audio_verified=False,limits='Trace records the existing refill-policy cursor only. A previous query may precede further submissions; any projected reserve assumes ideal44100Hz consumption, not measured acoustic output. In-memory writes still perturb timing. A clean run does not clear earlier failed acceptance.')
result.update(lowest_reserve_query=lowest,lowest_reserve_relative_producer_lateness_ms=late(lowest),maximum_relative_producer_lateness_ms=max(late(q) for q in valid),largest_service_gaps=service_gaps,producer_lateness_note='Relative to first existing valid query. Compares query timestamp with original game-step period; measures accumulated service lag change, not CPU-time attribution or audio latency.')
(out/'analysis-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
