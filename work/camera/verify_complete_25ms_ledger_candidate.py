import json,sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text());s=r['bounded_diagnostic_stats']['whole_run_api_intervals'];ledger=s['long_intervals']
assert ledger['capacity']==512 and ledger['dropped']==0 and ledger['total']==len(ledger['records'])==s['over_25ms']
assert 'Intervals>25ms' in ledger['scope']
assert all(q['interval_ns']>25000000 and q['interval_ns']==q['end_ns']-q['begin_ns'] and len(json.dumps(q,separators=(',',':'),allow_nan=False).encode())<=16384 for q in ledger['records'])
assert sum(q['interval_ns']*3>100000000 for q in ledger['records'])==s['over_33_333ms']
assert sum(q['interval_ns']>50000000 for q in ledger['records'])==s['over_50ms']
assert len({(q['epoch'],q['generation'],q['display_index']) for q in ledger['records']})==len(ledger['records'])
out=dict(result='PASS_COMPLETE_25MS_LEDGER_COVERAGE',retained=ledger['total'],over33=s['over_33_333ms'],over50=s['over_50ms'],dropped=ledger['dropped'],scope='Complete >25ms API interval evidence and threshold counters, bounded records/unique identities. No scanout or exclusive cause proof.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2));print(out)
