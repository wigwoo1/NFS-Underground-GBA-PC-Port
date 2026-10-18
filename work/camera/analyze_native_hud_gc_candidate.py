import json,sys,statistics
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());groups={};overlaps=[]
for row in r['presentation_samples']:
 p=next(x['profile'] for x in row['prepared']['consumer_stages'] if x['stage']=='hud_substages')
 for x in p:
  assert x['elapsed_ns']>=0;groups.setdefault(x['stage'],[]).append(x['elapsed_ns']/1e6)
 t=row['callback_timing']
 for gc in r['gc_collection_samples']:
  assert gc['start_ns']<=gc['end_ns']
  if gc['start_ns']<t['draw_end_ns'] and gc['end_ns']>t['draw_begin_ns']:overlaps.append(dict(index=row['display_index'],gc=gc))
gc_rows=r['gc_collection_samples']
gc_longest=sorted(gc_rows,key=lambda g:g['end_ns']-g['start_ns'],reverse=True)[:10]
previous=None;gap_rows=[]
for row in r['presentation_samples']:
 if row['native_result']!=1:continue
 if previous is not None and (row['epoch'],row['generation'])==(previous['epoch'],previous['generation']) and row['display_index']==previous['display_index']+1:
  begin=previous['callback_timing']['present_end_ns'];end=row['callback_timing']['present_end_ns']
  matched=[g for g in gc_rows if g['start_ns']<end and g['end_ns']>begin]
  gap_rows.append(dict(index=row['display_index'],gap_ms=(end-begin)/1e6,gc_overlap=matched))
 previous=row
result=dict(longest_gc=gc_longest,slowest_gaps=sorted(gap_rows,key=lambda x:x['gap_ms'],reverse=True)[:20],result='PASS_HUD_GC_DIAGNOSTICS',stages={k:dict(count=len(v),median_ms=statistics.median(v),max_ms=max(v)) for k,v in groups.items()},gc_rows=len(r['gc_collection_samples']),draw_gc_overlaps=overlaps,scope='Instrumented nested HUD wall intervals and observed parent GC overlap; correlation not cause, child collections separate, GPU execution unmeasured.')
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ('draw_gc_overlaps','longest_gc','slowest_gaps')},indent=2))
