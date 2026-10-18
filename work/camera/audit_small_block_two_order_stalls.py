import json
from pathlib import Path
p=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010');rows=[]
def refresh(x):return x[-1] if isinstance(x,list) else x
def ms(d,a,b):assert d[b]>=d[a];return (d[b]-d[a])/1e6
for order,name in [('baseline_first','small-block-live-comparison.json'),('candidate_first','small-block-reverse-comparison.json')]:
 comparison=json.loads((p/name).read_text())
 for run in comparison['runs']:
  r=json.loads(Path(run['raw']).read_text());ledger=r['live_observation_stats']['whole_run_api_intervals']['native_commit_long_intervals'];assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
  if not ledger['records']:rows.append(dict(order=order,variant=run['variant'],long_gaps=0));continue
  x=max(ledger['records'],key=lambda y:y['interval_ns']);older,newer=x['transaction']['commit'][2:4];jobs=[j for j in r['world_preparation_stage_samples'] if refresh(j['older'])==older and refresh(j['newer'])==newer];assert len(jobs)==1
  t=jobs[0]['terminal'][5];s=x['caller_stages'];c=x['caller_timing'];assert t['clean_request_close'];first=t['sample_transfer_rows'][0]
  rows.append(dict(order=order,variant=run['variant'],long_gaps=ledger['total'],older=older,newer=newer,gap_ms=x['interval_ns']/1e6,take_ms=ms(s,'preparation_take_begin_ns','preparation_take_end_ns'),draw_ms=ms(c,'draw_begin_ns','draw_end_ns'),construct_ms=ms(t,'initialized_ns','constructed_ns'),first_ready_ms=(first['ready_ns']-t['constructed_ns'])/1e6))
out=dict(result='PASS_SMALL_BLOCK_TWO_ORDER_WORST_JOINS',rows=rows,scope='Each actual retained largestlong nativegap joined exactcompletedsourcejob in4runs. Inclusivewall scopes/pipelineoverlap, no exclusiveCPUcause or guaranteedoptimizationbenefit; no60qualification.')
(p/'small-block-two-order-stall-joins.json').write_text(json.dumps(out,indent=2));print(out)
