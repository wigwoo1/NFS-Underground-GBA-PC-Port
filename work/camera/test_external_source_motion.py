import json,sys,struct,math
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_model_sources import OwnedModelSources
from owned_external_source_motion import PreparedExternalSourceMotion
from owned_scenery_motion import normalized_matrix
from owned_motion_pairs import records
report_path=Path(sys.argv[1]);r=json.loads(report_path.read_text());c=r['model_scene_captures'][1:3]
scenes=[ClosedGraph.decode(Path(x['graph']).read_bytes()) for x in c]
sources=[OwnedModelSources.decode(Path(x['current-sources']).read_bytes(),s) for x,s in zip(c,scenes)]
motion=PreparedExternalSourceMotion(scenes,sources,1)
matrices=[motion.matrix(i/100) for i in range(101)]
assert len(set(matrices))==101 and all(all(math.isfinite(v) for v in m) for m in matrices)
assert matrices[0]==normalized_matrix(motion.endpoint_poses[0]) and matrices[-1]==normalized_matrix(motion.endpoint_poses[1])
rows=records(Path(c[1]['frame']).read_bytes())['records']
assert any(row['kind']==3 and bytes(row['blocks'][2])==motion.endpoint_poses[1] for row in rows)
try:motion.matrix(float('nan'))
except ValueError:pass
else:raise AssertionError('Nonfinite alpha accepted')
try:PreparedExternalSourceMotion(scenes,list(reversed(sources)),1)
except ValueError:pass
else:raise AssertionError('Mismatched source clocks accepted')
evidence=dict(source=1,source_clocks=[s.graph.refresh for s in scenes],distinct_samples=101,exact_endpoints=True,newer_original_draw_exact=True,limitation='Transform component only; complete geometry, appearance clipping and live integration remain pending.')
report_path.with_suffix('.external-source-motion.json').write_text(json.dumps(evidence,indent=2))
print('PASS101 distinct external source rigid poses, exact endpoints and original newer draw')
