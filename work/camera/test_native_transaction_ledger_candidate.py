import copy,json
from pathlib import Path
from owned_native_transaction_interval_totals_candidate import LongIntervalTotals
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791567279013099100.json').read_text())
rows=r['presentation_samples'];ledger=LongIntervalTotals();expected=[]
previous=None
for row in rows:
 ledger.observe(row)
 if row['native_result']!=1:continue
 key=(row['epoch'],row['generation'],row['display_index']);stamp=row['commit'][6]
 if previous and key[:2]==previous[0][:2] and key[2]==previous[0][2]+1 and stamp-previous[1]>25000000:expected.append(stamp-previous[1])
 previous=(key,stamp)
stats=ledger.stats();events=stats['native_commit_long_intervals']
assert events['total']==len(expected) and [x['interval_ns'] for x in events['records']]==expected and events['dropped']==0
snapshot=copy.copy(ledger);snapshot.native_events.append(b'{}');assert len(snapshot.native_events)==len(ledger.native_events)+1
assert all(len(x)<=16384 for x in ledger.native_events)
out=dict(result='PASS_NATIVE_INTERVAL_LEDGER_RETAINED_ACTUAL_ROWS_AND_COPY',actual_rows=len(rows),actual_long_intervals=len(expected),scope='Independent retained-row commit delta comparison and private snapshot deque; whole-run no-drop coverage must be verified from live counters.')
Path('work/camera/prototype-runs/native-transaction-ledger-component-20261009.json').write_text(json.dumps(out,indent=2));print(out)
