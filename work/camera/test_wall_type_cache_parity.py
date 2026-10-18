import runpy,json
from pathlib import Path
import owned_wall_visibility_candidate as candidate
fixture=runpy.run_path('work/camera/test_wall_batch_domain_parity.py')
baseline=runpy.run_path('work/camera/owned_wall_visibility_candidate.py.before-type-cache')['batch']
counts=(0,1,4,12,25,31,64,128,512,4096);checked=0
for amount in counts:
 calls=[fixture['call'](edge=(float(i%17-8),float(i%19-9),float(400+i%1600),float(600+i%1700),0.,0.,1.,1.)) for i in range(amount)]
 expected=baseline(calls);actual=candidate.batch(calls);assert expected==actual;checked+=amount
 snapshot=actual;candidate.batch([fixture['call']()]*7);assert actual==snapshot
for amount in range(1,97):candidate.batch_types(amount)
assert candidate.batch_types.cache_info().currsize==64
input_type,output_type=candidate.batch_types(4);assert candidate.batch_types(4)==(input_type,output_type)
a,b=input_type(),input_type();a[0].flags=123;assert b[0].flags==0
x,y=output_type(),output_type();x[0].flags=123;assert y[0].flags==0
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/wall-type-cache-parity-20261007');cp.mkdir(exist_ok=True)
(cp/'result.json').write_text(json.dumps(dict(result='PASS',counts=counts,wall_classifications=checked,cache_types_bound=64,input_output_instances_private=True,scope='Native wall batch baseline classification parity and bounded class ownership; synthetic recovered-domain inputs, not full original game or live cadence proof.'),indent=2))
for name in ('test_wall_type_cache_parity.py','owned_wall_visibility_candidate.py'):(cp/name).write_bytes(Path('work/camera',name).read_bytes())
print('PASS',checked,'baseline wall classifications, 64-entry bound and private instances')