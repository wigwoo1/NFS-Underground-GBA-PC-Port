import sys,json
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());previous=None;gaps=[]
for row in r['presentation_samples']:
 if row['native_result']!=1:continue
 t=row['callback_timing']
 if previous is not None and (row['epoch'],row['generation'])==(previous['epoch'],previous['generation']) and row['display_index']==previous['display_index']+1:
  start=previous['callback_timing']['present_end_ns'];marks=[start,row['transaction_begin_ns'],t['draw_begin_ns'],t['draw_end_ns'],t['present_begin_ns'],t['present_end_ns']]
  assert marks==sorted(marks),row['display_index']
  names=('before_transaction','before_draw','draw_callback','wait_before_present','present_callback')
  parts={name:(marks[i+1]-marks[i])/1e6 for i,name in enumerate(names)};duration=(marks[-1]-start)/1e6
  assert abs(sum(parts.values())-duration)<1e-6
  stages=row['stages'];wait=row['wait']
  assert len(stages)==7 and stages==sorted(stages) and wait[0]<=wait[2]
  entry_ms=(t['present_begin_ns']-stages[3])/1e6
  assert entry_ms>=-.1
  native_detail=dict(deadline_wait_ms=(wait[2]-wait[0])/1e6,presentation_lock_ms=(stages[1]-stages[0])/1e6,state_lock_ms=(stages[2]-stages[1])/1e6,python_callback_entry_ms=max(0,entry_ms))
  jobs=[p for p in r['world_preparation_stage_samples'] if p['older']==row['source_older'] and p['newer']==row['refresh']]
  nearest=min(jobs,key=lambda p:abs(p['parent_completed_ns']-row['transaction_begin_ns'])) if jobs else None
  setup=row.get('source_setup_profile')
  setup_detail=None
  if setup is not None:
   setup_detail=dict(pair_take_ms=(setup['pair_ready_ns']-setup['pair_take_begin_ns'])/1e6,setup_total_ms=(setup['owned_ready_ns']-setup['setup_begin_ns'])/1e6,owned_context_ms=(setup['owned_ready_ns']-setup['sky_ready_ns'])/1e6,pair_ready_relative_to_previous_present_ms=(setup['pair_ready_ns']-start)/1e6,setup_begin_relative_to_previous_present_ms=(setup['setup_begin_ns']-start)/1e6)
  gaps.append(dict(source_setup=setup_detail,index=row['display_index'],duration_ms=duration,parts=parts,native_detail=native_detail,source_pair=[row['source_older'],row['refresh']],same_source_pair=row['source_older']==previous['source_older'] and row['refresh']==previous['refresh'],preparation_completed_relative_to_transaction_ms=None if nearest is None else (nearest['parent_completed_ns']-row['transaction_begin_ns'])/1e6,source_dequeue_relative_to_previous_present_ms=(row['source_dequeued_ns']-start)/1e6))
 previous=row
assert gaps
slow=sorted(gaps,key=lambda x:x['duration_ms'],reverse=True)[:20]
result=dict(result='PASS_FRAME_GAP_DECOMPOSITION',adjacent_intervals=len(gaps),slowest=slow,scope='Exact wall-time partition of adjacent successful presentations; before_transaction includes preparation wait, source setup, queue and scheduling. Matching preparation by refresh and nearest time is diagnostic association, not causal proof.')
Path(sys.argv[2]).write_text(json.dumps(result,indent=2));print(json.dumps(slow[:5],indent=2))
