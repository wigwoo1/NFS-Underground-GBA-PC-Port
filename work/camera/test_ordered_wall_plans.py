"""Preserve captured ordering; expose unsupported candidate insertion."""
from pathlib import Path
import copy, json
from ordered_wall_plans import assemble
p = Path('work/camera')
r = json.loads((p/'texture-provenance-tests.json').read_text())
dispatch = {x['serial']: x['commands'] for x in r['dispatch_samples']}
rows = []
for sample in r['portal_samples']:
    serial = 141 if sample['alpha'] == 1 else 140
    commands, plans = dispatch[serial], sample['all_wall_plans']
    saved = copy.deepcopy((commands, plans))
    result = assemble(commands, plans)
    assert (commands, plans) == saved
    indices = [x['captured_index'] for x in result['commands']]
    assert indices == sorted(set(indices))
    assert [x['command'] for x in result['commands'] if x['command'][0] != 2] == [c for c in commands if c[0] != 2]
    pending = [x['source'] for x in result['pending_insertion']]
    assert pending == ([139937176] if .78 <= sample['alpha'] < 1 else [])
    model = next(i for i,x in enumerate(result['commands']) if x['command'][0] == 3)
    obj = next(i for i,x in enumerate(result['commands']) if x['command'][2] == 139970292)
    assert (obj < model) == (serial == 140)
    if sample['alpha'] in (0, 1):
        assert result['complete'] and [x['command'] for x in result['commands']] == commands
    rows.append(dict(alpha=sample['alpha'], serial=serial, pending=pending, object_before_model=obj<model))
for bad in (dispatch[140]+[next(c for c in dispatch[140] if c[0]==2)], [c for c in dispatch[140] if c[0]!=3]):
    try: assemble(bad, [])
    except ValueError: pass
    else: raise AssertionError('invalid dispatch accepted')
try: assemble(dispatch[140], r['portal_samples'][0]['all_wall_plans']*2)
except ValueError: pass
else: raise AssertionError('duplicate plan accepted')
report = dict(result='PASS', samples=rows, rejection_cases=3,
              scope='Diagnostic ordering only; candidate insertion and interpolated object eligibility remain unresolved.')
(p/'ordered-wall-plan-tests.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
