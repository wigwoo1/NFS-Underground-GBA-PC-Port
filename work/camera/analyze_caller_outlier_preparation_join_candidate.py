import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());o=json.loads(Path(sys.argv[2]).read_text());assert o['dropped']==0 and o['totals']['bundle']==o['totals']['material']==r['presentations']
lookup={x['native_begin_ns']:x for x in o['outliers'] if x['kind']=='bundle'};assert len(lookup)==sum(x['kind']=='bundle' for x in o['outliers'])
ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals'];assert ledger['dropped']==0
rows=[]
for e in ledger['records']:
 c=e['caller_stages'];bundle=e['prepared']['bundle_transfer_profile'];commit=e['transaction']['commit'];matches=[p for p in r['world_preparation_stage_samples'] if [p['older'],p['newer']]==commit[2:4]];assert len(matches)==1;p=matches[0]
 assert c['preparation_take_begin_ns']<=c['preparation_take_end_ns']<=c['pair_ready_ns']
 x=bundle['caller_execution'];assert bundle['caller_begin_ns']<=x['before'][0]<=bundle['native_begin_ns']<=bundle['native_end_ns']<=x['after'][0]<=bundle['caller_end_ns']
 rows.append(dict(identity=[commit[0],commit[1],commit[4]],source_pair=commit[2:4],interval_ms=e['interval_ns']/1e6,preparation_take_wait_ms=(c['preparation_take_end_ns']-c['preparation_take_begin_ns'])/1e6,hud_wait_ms=(c['hud_prefetch_wait_end_ns']-c['hud_prefetch_wait_begin_ns'])/1e6,bundle_outer_return_ms=(bundle['caller_end_ns']-bundle['native_end_ns'])/1e6,bundle_is_return_outlier=bundle['native_begin_ns'] in lookup,preparation_job_ms=(p['completed_ns']-p['started_ns'])/1e6,child_construct_ms=(p['terminal'][5]['constructed_ns']-p['terminal'][5]['decoded_ns'])/1e6,parent_sample_rows=p['parent_sample_rows']))
out=dict(result='PASS_EXACT_LONG_FRAME_SOURCE_PREPARATION_JOIN',totals=o['totals'],return_outliers=len(o['outliers']),rows=rows,scope='Exact native commit source pair to retained parent preparation job and native bundle timestamps. Wait durations are observations; no exclusive scheduler/instrumentation/GIL causal claim. All four longframes retained.')
Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print(json.dumps({**{k:v for k,v in out.items() if k!='rows'},'rows':[{k:v for k,v in x.items() if k!='parent_sample_rows'} for x in rows]}))
