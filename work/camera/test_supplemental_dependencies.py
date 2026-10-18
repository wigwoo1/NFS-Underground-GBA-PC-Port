import json
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_supplemental_dependencies import dependencies
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text())
checks=[]
for frame in r['wall_diagnostic_frames']:
 closed=ClosedGraph.decode(Path(frame['graph']).read_bytes())
 deps=dependencies(closed)
 assert len(deps)==16
 assert len({(d.parent_descriptor,d.object_index) for d in deps})==16
 assert {d.descriptor for d in deps}=={90,*range(171,185),219}
 assert all(len(d.source)==164 and d.descriptor_address%4==0 for d in deps)
 checks.append(dict(refresh=closed.refresh,dependencies=[dict(parent=d.parent_descriptor,object=d.object_index,descriptor=d.descriptor,address=d.descriptor_address) for d in deps]))
out=dict(result='PASS_COMPLETE_SUPPLEMENTAL_DEPENDENCY_INVENTORY',scenes=len(checks),checks=checks,scope='Complete raw object dependency inventory; assets not yet captured and sampled dispatch not verified.')
Path('work/camera/supplemental-dependency-tests.json').write_text(json.dumps(out,indent=2))
print(out['result'],len(checks))
