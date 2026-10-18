"""Join active presentation stalls to actual completed child source pairs."""
import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());w=r['live_observation_stats']['whole_run_api_intervals'];ledger=w['native_commit_long_intervals']
assert ledger['dropped']==0
out=[]
for x in sorted(ledger['records'],key=lambda x:x['interval_ns'],reverse=True)[:10]:
 c=x['transaction']['commit'];older,newer=c[2:4]
 matched=[z for z in r['world_preparation_stage_samples'] if (z['older'][1] if isinstance(z['older'],list) else z['older'])==older and (z['newer'][1] if isinstance(z['newer'],list) else z['newer'])==newer]
 stages=x['caller_stages'];take=(stages['preparation_take_end_ns']-stages['preparation_take_begin_ns'])/1e6
 row=dict(older=older,newer=newer,gap_ms=x['interval_ns']/1e6,take_ms=take,matched_completed_jobs=len(matched))
 if len(matched)==1:
  d=matched[0]['terminal'][5];samples=d.get('sample_transfer_rows',[])
  assert d['child_started_ns']<=d['decoded_ns']<=d['initialized_ns']<=d['constructed_ns']
  row.update(child_construct_ms=(d['constructed_ns']-d['initialized_ns'])/1e6,construction_stages=d.get('construct_stages',[]),source_setup_stages=d.get('source_setup_stages',[]))
  if samples:
   first=samples[0];assert first['ready_ns']>=d['constructed_ns']
   gc=d.get('child_gc_trace');assert gc is None or gc.get('dropped',0)==0
   row.update(first_sample_ms=(first['ready_ns']-d['constructed_ns'])/1e6,first_sample_cpu_ms=None if first.get('prepare_cpu_ns') is None else first['prepare_cpu_ns']/1e6,first_sample_cycles=first.get('prepare_thread_cycles'),first_sample_gc_overlap_ms=None if gc is None else sum(max(0,min(first['ready_ns'],v['end_ns'])-max(d['constructed_ns'],v['start_ns'])) for v in gc.get('rows',[]))/1e6)
  timings=d.get('sample_timings',[])
  row['first_sample_stages']=timings[0].get('source_sample_stages',[]) if timings else []
  row['assembly_stages']=[{k:v for k,v in stage.items() if k in ('name','started_ns','completed_ns','wall_ns','thread_cycles','thread_cpu_ns','geometry_bytes','tail_bytes','frame_bytes','geometry_records')} for stage in (timings[0].get('assembly_stages',[]) if timings else [])]
  row['nested_assembly_stages']=[]
  for stage in (timings[0].get('assembly_stages',[]) if timings else []):
   for name in ('visibility_stages','road_stages','owner_stages'):
    for child in stage.get(name,[]):
     row['nested_assembly_stages'].append(dict(parent=stage['name'],**{k:v for k,v in child.items() if k in ('name','descriptor','wall_ns','thread_cycles','count')}))
 out.append(row)
result=dict(result='PASS_ACTIVE_GAP_COMPLETED_CHILD_JOINS',rows=out,active_intervals={k:v for k,v in w['all_successful_native_intervals'].items() if not isinstance(v,(dict,list))},scope='Largest ten active retained gaps, complete gap ledger. Child detail only for unique completed-job joins; missing jobs explicit. Inclusive source stages overlap publication and acknowledgement; trace overhead, not exclusive CPU or smooth60 qualification.')
Path(sys.argv[2]).write_text(json.dumps(result,indent=2))
print(result['result'])
for x in out[:3]:
 print('gap',round(x['gap_ms'],3),'pair',x['older'],x['newer'],'take',round(x['take_ms'],3),'child',round(x.get('child_construct_ms',0),3),'first',round(x.get('first_sample_ms',0),3),'gc',None if x.get('first_sample_gc_overlap_ms') is None else round(x['first_sample_gc_overlap_ms'],3))
 print('setup',[(s.get('name'),round(s.get('wall_ns',0)/1e6,3)) for s in x.get('source_setup_stages',[])])
 print('sample',[(s.get('name'),round(s.get('wall_ns',0)/1e6,3)) for s in x.get('first_sample_stages',[])])
