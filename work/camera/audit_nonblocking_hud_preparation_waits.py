import json
from pathlib import Path
root=Path(r'G:\EXTRA DATA DRIVE\Desktop\Games\Codex\NFSUG-Native-PC-Port\work\camera\prototype-runs')
out={}
for label in ('base','candidate_nonblocking'):
 manifest=json.loads((root/f'model-index-{"base" if label=="base" else "candidate"}60-clock-cleanup-20261010.json').read_text()) if label=='base' else None
 source=Path(manifest['source']) if manifest else root/'owned-native-1791680452940393300.json'
 raw=json.loads(source.read_text());w=raw['live_observation_stats']['whole_run_api_intervals']
 ledger=w['native_commit_long_intervals']; assert ledger['dropped']==0
 jobs={ (x['older'],x['newer']):x for x in raw['world_preparation_stage_samples'] }
 rows=[]
 for x in ledger['records']:
  pair=tuple(x['transaction']['commit'][2:4]);matches=[jobs[pair]] if pair in jobs else []
  assert len(matches)==1,(label,pair)
  req=matches[0];terminal=req['terminal'][5];st=x['caller_stages'];take=(st['preparation_take_end_ns']-st['preparation_take_begin_ns'])/1e6
  gc=terminal.get('child_gc_trace',{}).get('rows',[]);rb, re=req['submission_begin_ns'],req['completed_ns']
  overlap=[(max(rb,g['start_ns']),min(re,g['end_ns'])) for g in gc if max(rb,g['start_ns'])<min(re,g['end_ns'])]
  rows.append(dict(index=x['display_index'],gap_ms=x['interval_ns']/1e6,source_pair=list(pair),prepare_total_ms=(re-rb)/1e6,queue_ms=(req['started_ns']-req['enqueued_ns'])/1e6,worker_ms=(re-req['started_ns'])/1e6,parent_take_ms=take,child_gc_overlaps=len(overlap),hud_wait_elided=st.get('hud_prefetch_wait_elided'),hud_dispatch_ms=(st['hud_prefetch_dispatch']['completed_ns']-st['hud_prefetch_dispatch']['started_ns'])/1e6))
 out[label]=dict(over25=len(ledger['records']),mean_ms=w['mean_ms'],max_ms=w['max_ms'],over25_all=w['over_25ms'],over33_all=w['over_33_333ms'],over50_all=w['over_50ms'],interval_records=rows)
result=dict(comparison=out,scope='Retained all native-commit >25ms intervals, exact matching to one same-run child world-preparation request. Durations overlap and are not additive or exclusive CPU causality; no physical scanout claim.')
path=root/'nonblocking-hud-preparation-waits-20261010.json';path.write_text(json.dumps(result,indent=2))
print(json.dumps({k:{q:v for q,v in val.items() if q!='interval_records'} for k,val in out.items()},indent=2))
print('nonblocking rows flagged',sum(r['hud_wait_elided'] is True for r in out['candidate_nonblocking']['interval_records']),'of',len(out['candidate_nonblocking']['interval_records']))
print('candidate sample',json.dumps(out['candidate_nonblocking']['interval_records'][:4],separators=(',',':')))
print('saved',path)
