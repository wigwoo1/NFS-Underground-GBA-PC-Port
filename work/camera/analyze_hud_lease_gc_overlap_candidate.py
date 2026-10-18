import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());assert r['gc_trace_dropped']==0
rows=[x for x in r['presentation_samples'] if x.get('native_result')==1];slow=[]
for x in sorted(rows,key=lambda x:x['prepared']['source_prepare_ns'],reverse=True)[:10]:
 t=x['callback_timing'];a,b=t['draw_begin_ns'],t['draw_end_ns'];events=[]
 for g in r['gc_collection_samples']:
  overlap=max(0,min(b,g['end_ns'])-max(a,g['start_ns']))
  if overlap:events.append(dict(generation=g['generation'],thread_id=g['thread_id'],duration_ms=(g['end_ns']-g['start_ns'])/1e6,overlap_ms=overlap/1e6,collected=g['collected']))
 slow.append(dict(display_index=x['display_index'],source_ms=x['prepared']['source_prepare_ns']/1e6,draw_ms=(b-a)/1e6,gc_overlaps=events))
out=dict(result='RETAINED_HUD_SOURCE_SPIKES_GC_DRAW_OVERLAP',slowest_source_rows=slow,scope='GC overlap against outer draw interval; source start/end not recorded so cannot attribute exclusive source time or causal stall. Retained120rows only.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
