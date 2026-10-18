"""Measure captured live poses and scene membership; do not infer smoothness."""
from pathlib import Path
import csv, json, math, sys
p=Path('work/camera')
prefix=sys.argv[1]
sources=list(csv.DictReader((p/(prefix+'-source-sources.csv')).open()))
live=list(csv.DictReader((p/(prefix+'-live.csv')).open()))
selected=[]
for source in sources:
    matches=[r for r in live if int(r['ready']) and abs(float(r['target'])-float(source['target']))<1e-8]
    assert len(matches)==1
    selected.append(matches[0])
def distance(a,b,kind):
    return math.sqrt(sum((float(b[kind+'_'+axis])-float(a[kind+'_'+axis]))**2 for axis in 'xyz'))
objects=[distance(a,b,'object') for a,b in zip(selected,selected[1:])]
cameras=[distance(a,b,'camera') for a,b in zip(selected,selected[1:])]
packets=json.loads((p/(prefix+'-packet-tests.json')).read_text())['records']
report=dict(result='PASS',frames=len(selected),span_original_refreshes=float(sources[-1]['target'])-float(sources[0]['target']),
            object_step_world_units=objects,camera_step_world_units=cameras,
            object_path_world_units=sum(objects),camera_path_world_units=sum(cameras),
            moving_object_steps=sum(v>1e-6 for v in objects),
            memberships=[dict(index=r['index'],roads=r['road_surfaces'],walls=r['wall_surfaces'],models=r['models']) for r in packets],
            scope='Exact target-matched live pose movement and captured membership. Positive movement is not smoothness, original raster fidelity, or physical scanout proof.')
assert len(selected)==12 and all(math.isfinite(v) for v in objects+cameras)
(p/(prefix+'-motion-tests.json')).write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
