"""Scenery chain associations survive interpolation outside spatial polygons."""
import runpy
from owned_sampled_model_visit import sampled_model_visit
v=runpy.run_path('work/camera/audit_failed_model_association.py')
class Pair:pass
pair=Pair();pair.scenes=v['scenes'];pair.portal=v['portal']
positions=[]
for step in range(101):
 alpha=step/100
 for object_index in (31,34,37,44,48,0):
  visit=sampled_model_visit(pair,alpha,object_index)
  assert visit['object']==object_index
  if object_index in (31,48):assert visit['parent']==29
 positions.append(sampled_model_visit(pair,alpha,0)['depth'])
assert len(set(positions))==101
print('PASS: 606 source-owned visits; out-of-polygon scenery associations retained; player depth continues moving')
