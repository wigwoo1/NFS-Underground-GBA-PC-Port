"""Join independently owned sample margins to exact retained native time intervals."""
import json,sys
from pathlib import Path
raw=json.loads(Path(sys.argv[1]).read_text());m=json.loads(Path(sys.argv[2]).read_text())
from analyze_sample_readiness_margin_candidate import analyze
verified=analyze(raw,m)
ledger=raw['bounded_diagnostic_stats']['whole_run_api_intervals']['native_commit_long_intervals'];assert ledger['dropped']==0
rows=[]
for e in ledger['records']:
 a,b=e['begin_ns'],e['end_ns'];assert b-a==e['interval_ns']
 matches=[dict(x,call_ms=(x['returned_ns']-x['requested_ns'])/1e6,margin_ms=x['available_before_request_ns']/1e6) for x in m['rows'] if max(a,x['requested_ns'])<min(b,x['returned_ns'])]
 rows.append(dict(native_identity=[e['epoch'],e['generation'],e['display_index']],interval_ms=(b-a)/1e6,margin_calls=matches))
out=dict(result='PASS_NATIVE_GAP_SAMPLE_MARGIN_TIME_ASSOCIATIONS',verified=verified['groups'],rows=rows,scope='Every margin independently source/publication verified, then associated by overlap with retained native commit gap. Time association is not native source identity proof or exclusive cause. Empty margin overlap does not exclude other render stalls.')
Path(sys.argv[3]).write_text(json.dumps(out,indent=2));print(out['result']);print([(x['native_identity'],x['interval_ms'],[(m['kind'],m['identity'],m['margin_ms']) for m in x['margin_calls']]) for x in rows])
