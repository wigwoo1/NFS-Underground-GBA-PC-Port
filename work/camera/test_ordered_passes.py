"""Pass guard tests use captured plans; they do not claim native reconstruction."""
from pathlib import Path
import json,copy
from ordered_wall_plans import assemble,assemble_anchored
p=Path('work/camera');r=json.loads((p/'texture-provenance-tests.json').read_text())
checked=ambiguous=mutations=0
for s in r['dispatch_samples']:
    commands=s['commands'];passes=s['wall_passes']
    plans=[dict(source=c[2],object_dispatch=c[1] if c[5] else None,pass_id=int(bool(wp[1]))) for c,wp in zip(commands,passes) if c[0]==2]
    keys=[(c[2],bool(c[5])) for c in commands if c[0]==2]
    if len(keys)!=len(set(keys)):
        try: assemble(commands,plans,passes)
        except ValueError: ambiguous+=1
        else: raise AssertionError('ambiguous source accepted')
        continue
    result=assemble(commands,plans,passes)
    assert result['complete'] and [x['command'] for x in result['commands']]==commands
    checked+=1
    for index in range(len(plans)):
        bad=copy.deepcopy(plans);bad[index]['pass_id']^=1
        try: assemble(commands,bad,passes)
        except ValueError: mutations+=1
        else: raise AssertionError('pass switch accepted')
dispatch={s['serial']:s for s in r['dispatch_samples']}
for sample in r['portal_samples']:
    s=dispatch[141 if sample['alpha']==1 else 140]
    assert assemble_anchored(s['commands'],sample['all_wall_plans'],s['wall_passes'])['complete']
assert checked+ambiguous==206 and mutations>0
report=dict(result='PASS',captured_sequences_preserved=checked,ambiguous_sequences_rejected=ambiguous,pass_switches_rejected=mutations,native_sampled_plans_checked=17,scope='Captured roundtrip and negative guard tests plus existing17native sampled plans. Broader native reconstruction and pass migrations unresolved.')
(p/'ordered-pass-tests.json').write_text(json.dumps(report,indent=2));print(report)
