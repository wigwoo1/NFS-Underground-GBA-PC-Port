from pathlib import Path
exec(compile(Path('work/camera/test_supplemental_visit_order.py').read_text(),'fixture','exec'))
from owned_ordinary_model_visits import ordinary_model_visits
checks=[]
for endpoint,expected_ordinal in ((0,6),(1,1)):
 visits=ordinary_model_visits(scenes[endpoint],portal.sample(endpoint));assert len(visits)==1 and visits[0]['object']==0 and visits[0]['ordinal']==expected_ordinal
 checks.append({key:value for key,value in visits[0].items() if key!='source'})
Path('work/camera/ordinary-model-visit-tests.json').write_text(json.dumps(checks,indent=2));print('PASS source-owned car visits atordinal6and1; shared visited ownership prevents root-revisit duplicate')
