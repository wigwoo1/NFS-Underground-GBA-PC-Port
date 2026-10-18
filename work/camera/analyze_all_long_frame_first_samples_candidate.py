import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());ledger=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals'];assert ledger['dropped']==0
assert ledger['total']==len(ledger['records'])
rows=[]
for e in ledger['records']:
 commit=e['transaction']['commit'];c=e['caller_stages'];matches=[p for p in r['world_preparation_stage_samples'] if [p['older'],p['newer']]==commit[2:4]];assert len(matches)==1;p=matches[0];assert p['terminal'][1]==p['generation'];t=p['terminal'][5];start=p['parent_start_timing'];transfers=t['sample_transfer_rows'];assert transfers and [x['index'] for x in transfers]==list(range(len(transfers)))
 stamps=[start['pack_begin_ns'],start['packed_ns'],start['sent_ns'],t['child_started_ns'],t['decoded_ns'],t['initialized_ns'],t['constructed_ns'],transfers[0]['ready_ns']];assert stamps==sorted(stamps)
 labels=['parent_pack','parent_send','sent_to_child_start','decode','initialize','construct','first_sample_prepare'];stages={label:(b-a)/1e6 for label,a,b in zip(labels,stamps,stamps[1:])}
 assert sum(stages.values())==sum((b-a)/1e6 for a,b in zip(stamps,stamps[1:]))
 row=dict(result='PASS_EXACT_WORST_FRAME_FIRST_SAMPLE_PARTITION',identity=commit[:2]+[commit[4]],source_pair=commit[2:4],interval_ms=e['interval_ns']/1e6,prior_commit_to_pair_begin_ms=(c['pair_begin_ns']-e['begin_ns'])/1e6,preparation_take_wait_ms=(c['preparation_take_end_ns']-c['preparation_take_begin_ns'])/1e6,hud_wait_ms=(c['hud_prefetch_wait_end_ns']-c['hud_prefetch_wait_begin_ns'])/1e6,first_sample_path_ms=stages,scope='Exact worst commit sourcepair matched to retained child job and first sample; enqueue/start/sample stamps are wall intervals, not exclusive CPU/scheduler causal attribution.')
 
 row['preparation_generation']=p['generation'];rows.append(row)
out=dict(result='PASS_ALL_LONG_FRAME_FIRST_SAMPLE_JOINS',count=len(rows),rows=rows,scope='Complete native long-interval ledger, unique exact source pair matched to one retained preparation job; producer generation independently verified against terminal (distinct from render generation). Wall partitions, not exclusive CPU causes.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(json.dumps(out))
