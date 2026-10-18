import json
from pathlib import Path
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/live-sky-stage-reference-20261007');rows=json.loads((cp/'selected-sky-pixels-1791421692829884800.json').read_text())['records'];checks=[]
for a,b in zip(rows,rows[1:]):
 if (a['source_older'],a['refresh'])!=(b['source_older'],b['refresh']):continue
 expected=sum(pa['expected']!=pb['expected'] for pa,pb in zip(a['sky_reference_points'],b['sky_reference_points']));changed=sum(pa['stage']!=pb['stage'] for pa,pb in zip(a['sky_reference_points'],b['sky_reference_points']))
 assert not expected or changed
 checks.append(dict(previous=a['display_index'],current=b['display_index'],expected_changed_points=expected,stage_changed_points=changed))
(cp/'stage-motion.json').write_text(json.dumps(dict(result='PASS',transitions=checks,scope='Sky-stage pixels move where original palette reference changes; no final unoccluded/physical cadence certification.'),indent=2));print(len(checks),sum(x['expected_changed_points']>0 for x in checks))
