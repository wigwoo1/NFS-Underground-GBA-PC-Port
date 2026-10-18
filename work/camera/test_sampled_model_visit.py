from pathlib import Path
exec(compile(Path('work/camera/test_supplemental_visit_order.py').read_text(),'fixture','exec'))
from owned_sampled_model_visit import sampled_model_visit
out=[]
for i in range(101):
 alpha=i/100;visit=sampled_model_visit(pair,alpha);out.append(dict(alpha=alpha,parent=visit['parent'],ordinal=visit['ordinal'],distance=visit['distance']))
assert out[0]['parent']==24 and out[0]['ordinal']==6 and out[-1]['parent']==23 and out[-1]['ordinal']==1
Path('work/camera/sampled-model-visit-tests.json').write_text(json.dumps(out,indent=2));print('PASS101 sampled ordinary car association/visit selections with exact endpoint ownership')

visit=sampled_model_visit(pair,0);visit["dispatch"]["model"]=-1
assert sampled_model_visit(pair,0)["dispatch"]["model"]==7
cache=pair._ordinary_visit_cache
sampled_model_visit(pair,.5);assert pair._ordinary_visit_cache is cache
print("PASS immutable endpoint identity retention against returned dispatch mutation")
