import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,'work/camera');s={};exec(Path('work/camera/test_source_transition_adapter.py').read_text().split('try:',1)[0],s)
from owned_wall_projection import projected
from owned_wall_region_candidates import regions
pair=s['prepared'];portal=pair.pair.portal
try:
 graph=s['scenes'][0].graph.graph;draws,stats=projected(graph,s['table']);original=list(regions(graph,s['table']));sample=list(portal.sample(0))
 result=dict(original_projection=stats,original_selected=[dict(descriptor=w.descriptor,edge=w.edge,region=list(region),source=hashlib.sha256(w.vertices).hexdigest()) for _,region,w,_ in draws],original_regions=[list(x) for x in original],continuous_endpoint_regions=[list(x) for x in sample])
finally:pair.close();s['history'].close()
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/wall-original-admission-20261007');cp.mkdir(exist_ok=True);(cp/'admission.json').write_text(json.dumps(result,indent=2));print(json.dumps(dict(stats=stats,original_region_count=len(original),continuous_region_count=len(sample),selected=result['original_selected']),indent=2))
