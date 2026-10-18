"""Matched diagnostic timing and bounded child-memory evidence."""
import json,re,sys
from pathlib import Path
runs={}
for label,path in zip(('baseline','interval'),sys.argv[1:3]):
 log=Path(path).read_text();assert 'SMOKE_COMPLETE' in log and 'Traceback' not in log
 raw=Path(re.findall(r'[^\r\n]*owned-native-\d+\.json',log)[0].strip());d=json.loads(raw.read_text())
 api=d['bounded_diagnostic_stats']['whole_run_api_intervals'];ledger=api['native_commit_long_intervals']
 assert ledger['dropped']==0 and ledger['total']==len(ledger['records'])
 jobs=d['world_preparation_stage_samples'];pids={j['terminal'][5]['pid'] for j in jobs};assert len(pids)==1
 e=json.loads((raw.parent/('child-gc-interval-'+str(next(iter(pids)))+'.json')).read_text())
 assert e['restored'] and e['sampler_stopped'] and not e['memory_errors'] and e['automatic_gc_enabled'] and e['restored_thresholds']==e['previous_thresholds']
 assert e['candidate_thresholds'][2]==(e['previous_thresholds'][2] if label=='baseline' else 50)
 m=e['memory_samples'];assert len(m)>100
 begin=m[0]['time_ns'];windows=[]
 for lo,hi in [(0,25),(25,50),(50,75),(75,110)]:
  rows=[x['private_bytes'] for x in m if lo<=(x['time_ns']-begin)/1e9<hi]
  assert rows;windows.append(dict(seconds=[lo,hi],minimum=min(rows),maximum=max(rows),last=rows[-1]))
 gcrows=[]
 for j in jobs:
  g=j['terminal'][5]['child_gc_trace'];assert g['dropped']==0
  gcrows.extend(g['rows'])
 full=[g for g in gcrows if g['generation']==2]
 assert d['frame_preparation_shutdown']['joined'] and d['frame_preparation_shutdown']['pending']==0
 runs[label]=dict(raw=str(raw),native=api['native_commit_intervals'],retained_child_jobs=len(jobs),retained_gc_events=len(gcrows),retained_full_collections=len(full),retained_full_collection_max_ms=max([(g['end_ns']-g['start_ns'])/1e6 for g in full],default=0),memory_samples=len(m),memory_span_s=(m[-1]['time_ns']-begin)/1e9,memory_windows=windows,after_final_collection=e['memory_after_final_collection'],restored=True)
out=dict(result='PASS_MATCHED_CHILD_GC_TIMING_MEMORY_AUDIT',runs=runs,cadence_qualified=False,promoted=False,scope='Sequential100s same scene original timing with equivalent observer. Complete native gap ledger; child event totals limited to retained jobs. Memory windows are bounded observation, not proof of indefinite stability; no physical scanout or exclusive-cause claim.')
Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print(json.dumps({k:dict(native=v['native'],full_gc_max_ms=v['retained_full_collection_max_ms'],memory_windows=v['memory_windows']) for k,v in runs.items()}))
