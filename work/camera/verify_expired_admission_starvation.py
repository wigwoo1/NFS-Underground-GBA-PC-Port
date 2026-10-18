import json
from pathlib import Path
raw=Path('work/camera/prototype-runs/owned-native-1791634635935718400.json');r=json.loads(raw.read_text());ledger=Path('work/camera/prototype-runs/expired-admission-1791634636153856000.json');miss=json.loads(ledger.read_text());s=miss['stats'];records=miss['records'];a=r['bounded_diagnostic_stats']['whole_run_api_intervals']['all_successful_native_intervals'];adj=r['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_intervals']
assert s['dropped_records']==0 and len(records)==s['retired']==504
assert a['successful_samples']==5 and a['count']==4 and a['excluded_generation_discontinuities']==0
assert s['examined']==a['successful_samples']+s['retired']==509
commits=[x['native_transaction']['commit'] for x in r['presentation_samples'] if x['native_result']==1];assert len(commits)==5
actual=[(b[6]-x[6])/1e6 for x,b in zip(commits,commits[1:])];assert abs(max(actual)-a['max_ms'])<1e-8
last=commits[-1];after=[x for x in records if x['native'][5]>last[6]];assert after
trailing=max(x['native'][5] for x in after)-last[6]
out=dict(result='PASS_COMPLETE_ACCOUNTING_RENDER_STARVATION_FAIL',raw=str(raw.resolve()),ledger=str(ledger.resolve()),successful_presentations=5,missed_slots=504,examined=509,reported_between_successes_max_ms=a['max_ms'],native_retirement_observed_trailing_hold_ms=trailing/1e6,missed_slots_after_last_success=len(after),cadence_qualified=False,scope='All5successful native records and complete504retired ledger. Trailing hold measured through last actual native retirement, not report serialization time. Short inter-success gaps cannot qualify an interval that stops presenting. No scanout/game-clock qualification.')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/expired-admission-first-live-20261010/starvation-audit.json').write_text(json.dumps(out,indent=2));print(out['result'],round(trailing/1e6,3),'ms trailing hold')
