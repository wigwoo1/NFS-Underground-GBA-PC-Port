import runpy,sys
from pathlib import Path
from owned_model_sources import OwnedModelSources
from owned_external_model_visit import PreparedExternalModelVisit
v=runpy.run_path('work/camera/test_external_record_candidate.py');scenes=v['scenes'];sources=[OwnedModelSources.decode(Path(c['current-sources']).read_bytes(),s) for c,s in zip(v['captures'],scenes)]
prepared=PreparedExternalModelVisit(scenes,sources,1,v['rom']);visits=[prepared.sample(i/100,v['portal'].sample(i/100)) for i in range(101)]
assert all(x and x['object']==1 and x['parent']==23 and x['dispatch']['model']==7 for x in visits)
assert len({x['distance'] for x in visits})==101
assert prepared.sample(.5,[]) is None
visits[0]['dispatch']['model']=-1;assert prepared.sample(0,v['portal'].sample(0))['dispatch']['model']==7
print('PASS101 source-owned external visits, distinct ordering distances and portal absence rejection')
