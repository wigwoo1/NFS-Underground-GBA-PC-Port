import json,sys
from pathlib import Path
from analyze_consumer_gap_partition import analyze
r=json.loads(Path(sys.argv[1]).read_text());load=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8-sig'));g=analyze(r);rows={x['display_index']:x for x in r['presentation_samples'] if x.get('native_committed_sample')}
for gap in g['largest']:
 x=rows[gap['display_index']];end=x['native_committed_sample'][6];start=end-round(gap['gap_ms']*1e6)
 gap['cpu_intervals']=[dict(begin_ns=s['begin_ns'],end_ns=s['end_ns'],top=s['top'][:3]) for s in load['samples'] if s['begin_ns']<end and s['end_ns']>start]
 candidates=[p for p in r['world_preparation_stage_samples'] if (p['older'],p['newer'])==(x['source_older'],x['refresh']) and p['completed_ns']<=x['pair_ready_ns']]
 assert candidates
 p=max(candidates,key=lambda p:p['completed_ns']);gap['preparation']=dict(unfinished_ms=max(0,p['completed_ns']-x['pair_begin_ns'])/1e6,construct_ms=p['construct_advance_ns']/1e6,precompute_ms=p['precompute_ns']/1e6)
p=max(r['world_preparation_stage_samples'],key=lambda p:p['precompute_ns']);stages=[]
def visit(value,path='root'):
 if isinstance(value,dict):
  if 'name' in value and 'started_ns' in value and 'completed_ns' in value:stages.append(dict(path=path,name=value['name'],wall_ms=(value['completed_ns']-value['started_ns'])/1e6,thread_cycles=value.get('thread_cycles')))
  for k,v in value.items():visit(v,path+'.'+k)
 elif isinstance(value,list):
  for i,v in enumerate(value):visit(v,path+'['+str(i)+']')
visit(p)
result=dict(result='PASS_STAGE_LOAD_JOIN',stalls=g,max_precompute=dict(older=p['older'],newer=p['newer'],ms=p['precompute_ns']/1e6,largest_nested_stages=sorted(stages,key=lambda s:s['wall_ms'],reverse=True)[:12]),scope='Nested stage times overlap and must not be summed. CPU one-second observations are partial/coarse and not exclusive cause or GPU evidence.')
Path(sys.argv[3]).write_text(json.dumps(result,indent=2));print(json.dumps(dict(largest_stall=g['largest'][0],max_precompute=result['max_precompute']),indent=2))
