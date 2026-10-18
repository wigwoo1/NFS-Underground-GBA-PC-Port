"""Scene-local occurrence routing, not cross-scene wall correspondence."""
from pathlib import Path
import copy,json
from ordered_wall_plans import assemble
p=Path('work/camera');r=json.loads((p/'texture-provenance-tests.json').read_text())
checked=0;rejected=0
for s in r['dispatch_samples']:
    plans=[dict(captured_index=i,source=c[2],object_dispatch=c[1] if c[5] else None,pass_id=int(bool(wp[1]))) for i,(c,wp) in enumerate(zip(s['commands'],s['wall_passes'])) if c[0]==2]
    result=assemble(s['commands'],plans,s['wall_passes'],occurrences=True)
    assert result['complete'] and [x['command'] for x in result['commands']]==s['commands']
    checked+=1
    if s['serial']==53:
        sources=[x['source'] for x in plans]
        repeated=[x for x in plans if sources.count(x['source'])>1]
        assert repeated and len({x['captured_index'] for x in repeated})==len(repeated)
        for change in ({'captured_index':None},{'captured_index':9999},{'source':0},{'object_dispatch':999},{'pass_id':1}):
            bad=copy.deepcopy(plans);bad[0].update(change)
            try: assemble(s['commands'],bad,s['wall_passes'],occurrences=True)
            except ValueError: rejected+=1
            else: raise AssertionError('invalid occurrence accepted')
        try: assemble(s['commands'],plans+[plans[0]],s['wall_passes'],occurrences=True)
        except ValueError: rejected+=1
        else: raise AssertionError('duplicate occurrence accepted')
        # Remove one repeated draw only; the other occurrence must survive.
        dropped=repeated[0]['captured_index']
        subset=[x for x in plans if x['captured_index']!=dropped]
        output=assemble(s['commands'],subset,s['wall_passes'],occurrences=True)
        assert [x['captured_index'] for x in output['commands']]==[i for i in range(len(s['commands'])) if i!=dropped]
assert checked==206 and rejected==6
report=dict(result='PASS',captured_sequences_preserved=checked,invalid_cases_rejected=rejected,repeated_occurrence_removal=True,scope='Captured plans test scene-local routing only. No new native reconstruction or cross-scene occurrence matching.')
(p/'ordered-occurrence-tests.json').write_text(json.dumps(report,indent=2));print(report)
