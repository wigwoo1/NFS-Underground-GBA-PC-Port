from pathlib import Path
import copy,json
from ordered_wall_plans import assemble_anchored
p=Path('work/camera'); r=json.loads((p/'texture-provenance-tests.json').read_text())
d={s['serial']:s['commands'] for s in r['dispatch_samples']}
rows=[]
for s in r['portal_samples']:
    serial=141 if s['alpha']==1 else 140
    result=assemble_anchored(d[serial],s['all_wall_plans'])
    assert result['complete']
    world=[(x['command'][0],x['command'][2]) for x in result['commands'] if x['command'][0]!=3]
    expected=d[141 if s['alpha']>=.78 else 140]
    assert world==[(c[0],c[2]) for c in expected if c[0]!=3]
    retained=[x['command'] for x in result['commands'] if x['captured_index'] is not None]
    assert retained==d[serial]
    rows.append(dict(alpha=s['alpha'],inserted=sum(x['captured_index'] is None for x in result['commands'])))
plans=r['portal_samples'][6]['all_wall_plans']
for changes in ({'pass_id':1},{'region':999},{'source':0xffffffff}):
    altered=copy.deepcopy(plans)
    next(x for x in altered if x['source']==139937176).update(changes)
    assert not assemble_anchored(d[140],altered)['complete']
report=dict(result='PASS',samples=rows,unsupported_cases=3,scope='Anchored first-pass insertion diagnostic; world source order matches endpoint capture. Model/object ordering remains retained, not recomputed.')
(p/'anchored-wall-plan-tests.json').write_text(json.dumps(report,indent=2))
print(report)
