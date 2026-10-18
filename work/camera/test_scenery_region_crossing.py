"""Source scenery crosses an original region edge with sampled moving position."""
import runpy,sys
sys.argv=['audit','work/camera/prototype-runs/fullscene-failure-1791283109682770300']
v=runpy.run_path('work/camera/audit_failed_model_association.py')
from owned_sampled_model_visit import sampled_model_visit
class Pair:pass
pair=Pair();pair.scenes=v['scenes'];pair.portal=v['portal'];parents=[];depths=[]
for step in range(101):
 visit=sampled_model_visit(pair,step/100,37);parents.append(visit['parent']);depths.append(visit['depth'])
assert parents[0]==31 and parents[-1]==29 and set(parents)=={29,31}
assert sum(a!=b for a,b in zip(parents,parents[1:]))==1
assert len(set(depths))==101
print('PASS: 101 moving scenery samples, one source-verified31->29 spatial crossing')
