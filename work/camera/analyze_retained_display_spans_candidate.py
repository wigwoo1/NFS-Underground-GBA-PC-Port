"""Correlate retained native sample identities without inventing missing stage times."""
import json,sys
from pathlib import Path
def overlap(a,b,c,d):return max(0,min(b,d)-max(a,c))
r=json.loads(Path(sys.argv[1]).read_text());assert r['gc_trace_dropped']==0
presentations={(x['epoch'],x['generation'],x['display_index']):x for x in r['presentation_samples']}
rows=[]
for span in r['dxgi_display_progress']['excess_refresh_spans']:
 sample=span['newer_native_sample'];key=None if sample is None else tuple(sample[k] for k in ('epoch','generation','display_index'));row=presentations.get(key)
 detail=None
 if row:
  t=row['callback_timing'];draw_start=t['draw_begin_ns'];draw_end=t['draw_end_ns'];present_start=t['present_begin_ns'];present_end=t['present_end_ns']
  hits=[dict(generation=g['generation'],thread_id=g['thread_id'],draw_overlap_ns=overlap(draw_start,draw_end,g['start_ns'],g['end_ns']),present_overlap_ns=overlap(present_start,present_end,g['start_ns'],g['end_ns']),duration_ns=g['end_ns']-g['start_ns']) for g in r['gc_collection_samples'] if overlap(draw_start,present_end,g['start_ns'],g['end_ns'])]
  detail=dict(draw_ns=draw_end-draw_start,present_ns=present_end-present_start,source_prepare_ns=row['prepared']['source_prepare_ns'],consumer_stage_costs=row['prepared']['consumer_stages'],deadline_lateness_at_draw_ns=draw_start-row['presentation_deadline_ns'],gc_overlaps=hits,stage_timestamp_scope='Consumer stages have durations only; no individual stage GC overlap attribution.')
 rows.append(dict(span=span,retained_native_detail=detail))
matched=[x for x in rows if x['retained_native_detail']]
out=dict(result='ANALYZED_RETAINED_DISPLAY_SPANS',span_count=len(rows),matched_count=len(matched),missing_count=len(rows)-len(matched),matches=rows,scope='Native identities correlate retained preparation/draw/present and GC intervals. Sparse retained window; unmatched spans explicit. Neither exclusive causality nor physical pixel certification.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(dict(span_count=len(rows),matched_count=len(matched),matched_details=[x['retained_native_detail'] for x in matched]),indent=2))
