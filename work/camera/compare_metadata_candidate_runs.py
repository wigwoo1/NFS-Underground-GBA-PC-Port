import json,sys,statistics
from pathlib import Path
from analyze_active_play_cadence import analyze
def summarize(path):
 r=json.loads(Path(path).read_text());all_gc=r['gc_collection_samples'];commits=[x['native_committed_sample'][6] for x in r['presentation_samples'] if x.get('native_committed_sample')];gc=[x for x in all_gc if x['start_ns']<commits[-1] and x['end_ns']>commits[0]];dec=[];prep=[];copied=0
 for p in r['world_preparation_stage_samples']:
  if p.get('history_only'):continue
  prep.append(p['precompute_ns']/1e6)
  for s in p.get('sample_timings',[]):
   for t in s.get('source_sample_stages',[]):
    for a in t.get('anchor_stages',[]):
     dec.extend(m['wall_ns']/1e6 for m in a.get('metadata_stages',[]) if m['name']=='uncached_decode')
 def stats(x):return dict(count=len(x),median_ms=statistics.median(x),p95_ms=sorted(x)[int(.95*(len(x)-1))],max_ms=max(x)) if x else None
 return dict(report=path,updates=r['original_updates'],scenes=r['owned_scene_submissions'],cadence=analyze(r),decode=stats(dec),precompute=stats(prep),gc_dropped=r['gc_trace_dropped'],gc_scope='Collections overlapping first-to-last committed presentation, excluding startup/shutdown; includes intentional pauses',gc_outside_play=len(all_gc)-len(gc),gc_generation_counts={str(g):sum(x['generation']==g for x in gc) for g in range(3)},gc_total_ms=sum(x['end_ns']-x['start_ns'] for x in gc)/1e6,gc_full=stats([(x['end_ns']-x['start_ns'])/1e6 for x in gc if x['generation']==2]))
out=dict(baseline=summarize(sys.argv[1]),candidate=summarize(sys.argv[2]),scope='Sequential recorded same-script/configuration runs; external load not controlled, no causal or scanout certification')
Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
