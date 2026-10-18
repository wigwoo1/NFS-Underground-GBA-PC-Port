import json
from pathlib import Path
p=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010')
comparison=json.loads((p/'native-range-reverse-comparison.json').read_text())
r=json.loads(Path(next(x['raw'] for x in comparison['runs'] if x['variant']=='candidate')).read_text())
ledger=r['live_observation_stats']['whole_run_api_intervals']['native_commit_long_intervals']
assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])==2
rows=[]
def refresh(x):return x[-1] if isinstance(x,list) else x
def span(x,a,b):
 assert x[b]>=x[a]
 return (x[b]-x[a])/1e6
for x in ledger['records']:
 commit=x['transaction']['commit'];older,newer=commit[2:4]
 jobs=[j for j in r['world_preparation_stage_samples'] if refresh(j['older'])==older and refresh(j['newer'])==newer]
 assert len(jobs)==1
 job=jobs[0];t=job['terminal'][5];s=x['caller_stages'];c=x['caller_timing'];presentation=x['transaction']['presentation']['present_stage_ns'];d=x['transaction']['renderer_dispatch']
 assert t['native_range_memory_stats']['constructions']>0 and t['clean_request_close']
 rows.append(dict(older=older,newer=newer,display_index=x['display_index'],gap_ms=x['interval_ns']/1e6,before_pair_ms=(s['pair_begin_ns']-x['begin_ns'])/1e6,pair_ms=span(s,'pair_begin_ns','pair_ready_ns'),take_ms=span(s,'preparation_take_begin_ns','preparation_take_end_ns'),hud_prefetch_wait_ms=span(s,'hud_prefetch_wait_begin_ns','hud_prefetch_wait_end_ns'),sky_ms=span(s,'sky_begin_ns','sky_end_ns'),draw_ms=span(c,'draw_begin_ns','draw_end_ns'),native_present_ms=span(presentation,'pumped','presented'),present_dispatch_wait_ms=span(d,'submitted_ns','started_ns'),child_construct_ms=span(t,'initialized_ns','constructed_ns'),first_ready_ms=(t['sample_transfer_rows'][0]['ready_ns']-t['constructed_ns'])/1e6))
result=dict(result='PASS_REVERSE_NATIVE_RANGE_STALL_JOINS',rows=rows,scope='Actual retained two long gaps joined to exact completed source jobs; overlapping inclusive wall spans, not exclusive CPU attribution. No sustained60 proof.',next_dependency='Inspect pair preparation and HUD prefetch/draw dispatch timings on diverse default-path captures; native range collection is not a demonstrated cure.')
(p/'native-range-reverse-stall-joins.json').write_text(json.dumps(result,indent=2));print(result)
