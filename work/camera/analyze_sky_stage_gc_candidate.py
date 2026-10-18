import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());stats=r['bounded_diagnostic_stats']['whole_run_api_intervals'];gaps=stats['slow_gap_samples'];gc=r['gc_collection_samples'];pauses=r['pause_events']
assert not r['gc_trace_dropped'] and not stats['slow_gap_dropped']
def overlaps(a,b,c,d):return max(0,min(b,d)-max(a,c))
rows=[]
for span in r['dxgi_display_progress']['excess_refresh_spans']:
 start=span['start_qpc']*1000000000//span['qpc_frequency'];end=span['end_qpc']*1000000000//span['qpc_frequency'];sample=span['newer_native_sample'];pause=sum(overlaps(start,end,p['begin_ns'],p['end_ns']) for p in pauses);matched=[g for g in gaps if sample and (g['epoch'],g['generation'],g['display_index'])==(sample['epoch'],sample['generation'],sample['display_index'])]
 detail=[]
 for gap in matched:
  stages=[]
  for name,wall in gap['stage_cost_ns'].items():
   finish=gap['stage_end_ns'].get(name);cycles=gap['stage_thread_cycles'].get(name)
   hits=[] if finish is None else [dict(generation=g['generation'],thread_id=g['thread_id'],overlap_ns=overlaps(finish-wall,finish,g['start_ns'],g['end_ns']),duration_ns=g['end_ns']-g['start_ns']) for g in gc if overlaps(finish-wall,finish,g['start_ns'],g['end_ns'])]
   stages.append(dict(stage=name,wall_ns=wall,thread_cycles=cycles,gc_overlaps=hits))
  detail.append(dict(display_index=gap['display_index'],draw_ns=gap['draw_ns'],present_ns=gap['present_ns'],stages=stages))
 rows.append(dict(span=span,pause_overlap_ns=pause,matched_slow_gap=detail))
out=dict(result='ANALYZED_DISPLAY_STAGE_GC_CORRELATION',spans=rows,scope='Scheduler QPC sample span matched to native submission identity and bounded slow API journal. GC overlap correlation is not exclusive causality; raw thread cycles are not converted to elapsed time. Missing matched stage evidence stays explicit.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
