import runpy
from owned_sampled_model_visit import sampled_model_visit
v=runpy.run_path('work/camera/audit_multicar_source_identity.py');pair=v['pair']
for object_index,model in ((0,7),(44,35)):
 samples=[sampled_model_visit(pair,i/100,object_index) for i in range(101)]
 assert all(s['object']==object_index and s['dispatch']['model']==model for s in samples)
 assert samples[0]['parent']==samples[-1]['parent']==(28 if object_index==0 else 29)
 assert samples[0]['ordinal']==samples[-1]['ordinal']==(0 if object_index==0 else 4)
 samples[0]['dispatch']['model']=-1;assert sampled_model_visit(pair,0,object_index)['dispatch']['model']==model
try:sampled_model_visit(pair,.5,999)
except ValueError:pass
else:raise AssertionError('Missing owned model accepted')
print('PASS202 independent player/scenery model source visits and missing-identity rejection')

from owned_model_record_owners import model_record_owners
owners=model_record_owners(pair,v['rom'])
assert dict(owners[0])=={17:44,18:0} and dict(owners[1])=={20:44,21:0}
print('PASS paired two-model source descriptor ownership and pose pairing')

