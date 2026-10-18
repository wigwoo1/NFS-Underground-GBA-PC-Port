"""Report queue-plan coverage against captured endpoint wall draws."""
from pathlib import Path
from collections import Counter
import json
p=Path('work/camera');r=json.loads((p/'texture-provenance-tests.json').read_text());rows=[]
for serial,index in [(140,0),(141,-1)]:
 actual={(x['identity'][2],tuple(x['bounds'])) for x in r['draw_bounds'] if x['serial']==serial and x['identity'][0]==2}
 planned=r['portal_samples'][index]['all_wall_plans'];predicted={(x['source'],tuple(x['viewport'])) for x in planned}
 actual_counts=Counter((x['identity'][2],tuple(x['bounds'])) for x in r['draw_bounds'] if x['serial']==serial and x['identity'][0]==2)
 predicted_counts=Counter((x['source'],tuple(x['viewport'])) for x in planned)
 assert actual_counts==predicted_counts
 missing=sorted(actual-predicted);extra=sorted(predicted-actual)
 assert missing==[]
 assert extra==[]
 rows.append(dict(serial=serial,missing=missing,extra=extra,planned_draws=len(planned)))
assert all(x['region']==181 and x['owner']==x['args'][1] for x in r['missing_wall_trace'])
report=dict(result='PASS',missing_wall_trace=r['missing_wall_trace'],endpoint_wall_identity_bounds_complete=True,interpolated_dispatch_verified=False,endpoints=rows,samples=[dict(alpha=s['alpha'],draw_count=len(s['all_wall_plans']),repeated_sources=[k for k,v in Counter(x['source'] for x in s['all_wall_plans']).items() if v>1]) for s in r['portal_samples']],scope='Endpoint wall identity/bounds coverage with retained object dispatch. Not full scene or interpolated object eligibility proof.')
(p/'wall-plan-coverage-tests.json').write_text(json.dumps(report,indent=2));print(rows)
