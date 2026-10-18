"""Correlate source metadata decode intervals with observed GC; no policy change."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());collections=r.get('gc_collection_samples',[]);rows=[]
for pair in r['world_preparation_stage_samples']:
 for sample in pair.get('sample_timings',[]):
  for stage in sample.get('source_sample_stages',[]):
   for anchor in stage.get('anchor_stages',[]):
    for m in anchor.get('metadata_stages',[]):
     if m['name']!='uncached_decode':continue
     gc=[g for g in collections if g['start_ns']<m['completed_ns'] and g['end_ns']>m['started_ns']]
     overlap=sum(max(0,min(m['completed_ns'],g['end_ns'])-max(m['started_ns'],g['start_ns'])) for g in gc)
     rows.append(dict(older=pair['older'],newer=pair['newer'],alpha=sample['alpha'],decode_ms=m['wall_ns']/1e6,decode_thread_cycles=m['thread_cycles'],gc_overlap_ms=overlap/1e6,collections=gc))
out=dict(result='OBSERVED',decode_count=len(rows),collections=len(collections),gc_trace_dropped=r.get('gc_trace_dropped'),largest=sorted(rows,key=lambda x:x['decode_ms'],reverse=True)[:20],scope='Recorded wall interval overlap is evidence of collection inside decode, not proof GC is sole stall cause; missing or dropped traces cannot exclude collection')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
