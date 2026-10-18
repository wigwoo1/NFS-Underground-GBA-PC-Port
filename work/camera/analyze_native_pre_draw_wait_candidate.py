import json,sys
from pathlib import Path
def analyze(r):
 assert r['result']=='SMOKE_COMPLETE'
 native=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals'];slow=r['preparation_retention']['slow_process_intervals']
 assert native['dropped']==slow['dropped']==0
 output=[]
 for event in native['records']:
  a=event['begin_ns'];b=event['caller_timing']['draw_begin_ns'];c=event['caller_stages'];assert b<=event['end_ns']
  names=['prior_to_pair','pair_to_take','preparation_future','take_to_hud','hud_future','hud_to_pair_ready','pair_ready_to_slot','sample','sample_to_sky','sky','sky_to_owner','owner','owner_to_lock','lock','lock_to_draw']
  values=[a,c['pair_begin_ns'],c['preparation_take_begin_ns'],c['preparation_take_end_ns'],c['hud_prefetch_wait_begin_ns'],c['hud_prefetch_wait_end_ns'],c['pair_ready_ns'],c['slot_begin_ns'],c['sample_end_ns'],c['sky_begin_ns'],c['sky_end_ns'],c['owner_begin_ns'],c['owner_end_ns'],c['lock_begin_ns'],c['lock_acquired_ns'],b]
  values=[max(a,min(b,x)) for x in values];assert values==sorted(values);parts=dict(zip(names,[y-x for x,y in zip(values,values[1:])]))
  assert sum(parts.values())==b-a
  older,newer=event['transaction']['commit'][2:4]
  matches=[x for x in slow['records'] if (x['older'],x['newer'])==(older,newer) and x['begin_ns']<=c['preparation_take_end_ns'] and x['end_ns']>=c['preparation_take_begin_ns']]
  assert len(matches)<=1
  child=None
  if matches:
   x=matches[0];assert not x['stage_records_truncated'] and x['child_gc_dropped']==0
   boundaries=x['child_boundaries'];begin=c['preparation_take_begin_ns'];end=c['preparation_take_end_ns']
   ticks=[begin,boundaries['started_ns'],boundaries['decoded_ns'],boundaries['constructed_ns'],boundaries['sampled_ns'],boundaries['encoded_ns'],boundaries['sent_ns'],x['parent_received_ns'],x['end_ns'],end]
   clipped=[max(begin,min(end,t)) for t in ticks];assert clipped==sorted(clipped)
   spans=[y-x for x,y in zip(clipped,clipped[1:])];assert sum(spans)==end-begin
   samples=[]
   for sample in x['sample_stages']:
    for stage in sample['stages']:
     overlap=max(0,min(end,stage['completed_ns'])-max(begin,stage['started_ns']))
     if overlap:samples.append(dict(alpha=sample['alpha'],phase=stage['name'],overlap_ms=overlap/1e6,wall_ms=stage['wall_ns']/1e6,thread_cycles=stage['thread_cycles']))
   child=dict(identity=[older,newer],partition_ms=[v/1e6 for v in spans],sample_overlaps=samples)
  output.append(dict(index=event['display_index'],pre_draw_ms=(b-a)/1e6,parts_ms={k:v/1e6 for k,v in parts.items()},child=child))
 return dict(result='PASS_NATIVE_PRE_DRAW_EXACT_PARTITIONS',rows=output,child_phase_order=['before_child','decode','construct','precompute','encode','send','receive','parent_decode','future_return'],scope='Exact clipped caller pre-draw partition and matched slow request wait partition; child phases may overlap parent wait and must not be summed with it. No exclusive scheduling/algorithm cause or visible60 claim.')
if __name__=='__main__':
 out=analyze(json.loads(Path(sys.argv[1]).read_text()));Path(sys.argv[2]).write_text(json.dumps(out,indent=2))
 print(out['result'])
 for row in sorted(out['rows'],key=lambda x:x['pre_draw_ms'],reverse=True)[:3]:print(row)
