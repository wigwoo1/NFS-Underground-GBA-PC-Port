import json,sys,statistics,collections
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());stages=collections.defaultdict(list)
for row in r['presentation_samples']:
 for entry in (row.get('prepared') or {}).get('consumer_stages',[]):
  if 'thread_cycles' not in entry:continue
  assert entry['elapsed_ns']>=0 and entry['thread_cycles']>=0
  stages[entry['stage']].append(dict(ms=entry['elapsed_ns']/1e6,cycles=entry['thread_cycles'],index=row['display_index']))
def stats(v):
 a=sorted(x['ms'] for x in v);return dict(count=len(a),median_ms=statistics.median(a),p95_ms=a[min(len(a)-1,int(len(a)*.95))],max_ms=a[-1],largest=sorted(v,key=lambda x:x['ms'],reverse=True)[:5])
required=['source_state_copy','target_clear','backdrop_source_copy','backdrop_vector_prepare','backdrop_profile_enable','backdrop_draw_call']
assert all(stages[x] for x in required)
out=dict(result='PASS_FINE_STAGE_TELEMETRY',stages={k:stats(v) for k,v in stages.items()},scope='Owner-thread wall intervals include profiling overhead, scheduling and driver waits; execution cycles cannot independently distinguish GIL waiting or CPU frequency. No visible cadence proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2))
for k in required:print(k, {a:b for a,b in out['stages'][k].items() if a!='largest'})
