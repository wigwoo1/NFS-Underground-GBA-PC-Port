"""Complete slow-source ledger plus bounded decoder/GC overlap."""
import json,re,sys
from pathlib import Path
log=Path(sys.argv[1]).read_text();assert 'SMOKE_COMPLETE' in log and 'Traceback' not in log
raw=Path(re.findall(r'[^\r\n]*owned-native-\d+\.json',log)[0].strip());d=json.loads(raw.read_text())
slow=d['producer_retention']['long_scene_preparations'];assert slow['dropped']==0 and slow['total']==len(slow['records'])
assert d['gc_trace_dropped']==0
api=d['bounded_diagnostic_stats']['whole_run_api_intervals'];ledger=api['native_commit_long_intervals'];assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
rows=[]
for r in slow['records']:
 t=r['supplement_decode_trace'];assert t['refresh']==r['refresh']
 stages=t['stages'];assert [x['name'] for x in stages]==['header_sections','geometry_validation','owned_dependencies','owned_states','rom_source_edges','texture_validation','complete']
 assert all(x['completed_ns']>=x['started_ns'] and x['wall_ns']==x['completed_ns']-x['started_ns'] for x in stages)
 assert all(a['completed_ns']==b['started_ns'] for a,b in zip(stages,stages[1:]))
 detail=[]
 for s in stages:
  overlaps=[]
  for g in d['gc_collection_samples']:
   n=max(0,min(s['completed_ns'],g['end_ns'])-max(s['started_ns'],g['start_ns']))
   if n:overlaps.append(dict(generation=g['generation'],overlap_ms=n/1e6,thread_id=g['thread_id'],collected=g['collected']))
  assert s['thread_cpu_ns']>=0 and s['thread_cycles']>=0
  detail.append(dict(name=s['name'],wall_ms=s['wall_ns']/1e6,thread_cpu_ms=s['thread_cpu_ns']/1e6,thread_cycles=s['thread_cycles'],gc_overlaps=overlaps))
 rows.append(dict(refresh=r['refresh'],producer_ms=r['ns']/1e6,supplement_ms=r['stages']['supplement_decode_ns']/1e6,other_stages_ms={k:v/1e6 for k,v in r['stages'].items()},decode_stages=detail))
rows.sort(key=lambda r:r['supplement_ms'],reverse=True)
out=dict(result='PASS_LIVE_SLOW_DECODER_CPU_CYCLE_AUDIT',raw=str(raw),slow_source_count=slow['total'],native=api['native_commit_intervals'],gc_events=len(d['gc_collection_samples']),rows=rows,cadence_qualified=False,scope='All slow source records only with zero ledger drops; ordinary fast producers are not fully retained. GC overlap is temporal evidence, not exclusive cause or a verified remedy. Thread CPU clock may resolve to zero; raw cycles are not converted to time.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(dict(native=out['native'],slow_source_count=out['slow_source_count'],top_decode=rows[:3])))
