import json
from pathlib import Path
ledger=Path('work/camera/prototype-runs/expired-admission-1791634438971354400.json');r=json.loads(ledger.read_text());s=r['stats'];assert s['dropped_records']==0 and s['retired']==len(r['records'])==321 and s['cancelled']==0
for row in r['records']:
 n=row['native'];assert n[:4]==[row['epoch'],row['generation'],row['index'],row['index']] and n[4]==row['deadline_ns'] and n[5]>n[4]
 assert row['deadline_ns']==row['origin']+(row['index']*1000000000+59)//60 and 0<=row['alpha']<=1
raw=Path('work/camera/prototype-runs/owned-native-1791634438595419900.json');game=json.loads(raw.read_text());a=game['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_intervals']
success=a['count']+a['excluded']+1;assert success==250 and success+s['retired']==s['examined']==571
recent=[x['native_transaction']['commit'] for x in game['presentation_samples'] if x['native_result']==1];gaps=[]
for x,y in zip(recent,recent[1:]):
 if x[:2]==y[:2]:
  assert y[7]==x[7]+1
  gaps.append(dict(index_delta=y[4]-x[4],completion_gap_ms=(y[6]-x[6])/1e6))
out=dict(result='PASS_EXPLICIT_MISSED_SLOT_ACCOUNTING_CADENCE_FAIL',raw=str(raw.resolve()),ledger=str(ledger.resolve()),examined_slots=s['examined'],missed_slots=s['retired'],successful_presentations=success,retained_successful_window=len(recent),retained_max_gap_including_skips_ms=max(x['completion_gap_ms'] for x in gaps),adjacent_only_interval_count=a['count'],excluded_index_discontinuities=a['excluded'],cadence_qualified=False,scope='Complete321missed ledger;571examined=250successful+321retired. Deadline/identity/expiry verified. Reported adjacent-only gaps exclude7 discontinuities; cannot infer60fps. Recent120 successful timestamps include skipped-index gaps, not whole-run qualification. Original game timing/throughput not independently proven here.')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/pooled-retirement-component-20261010/live-expired-admission-audit.json').write_text(json.dumps(out,indent=2));print(out['result'],out['retained_max_gap_including_skips_ms'])
