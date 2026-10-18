import ctypes as C,json,runpy
from pathlib import Path
from unittest.mock import patch
import owned_source_face_mask_candidate as current
baseline={};exec(Path(str(Path(current.__file__))+'.before-type-cache').read_text(),baseline)
class Classifier:
 def combined_decisions(self,m,a,r):return (True,False,True),(0,4,4)
checks=0
for amount in range(0,145):
 rows=[dict(kind=3,key='model') for _ in range(amount)]
 models=[0.]*(12*amount);bounds=[0.,1.,0.,1.]*amount
 with patch.object(current,'records',return_value=dict(records=rows)),patch.dict(baseline,records=lambda frame:dict(records=rows)):
  a=current.build_source_face_mask(b'',models,bounds,.5,{'model':Classifier()});b=baseline['build_source_face_mask'](b'',models,bounds,.5,{'model':Classifier()})
  assert (bytes(a[0]),bytes(a[1]),a[2:])==(bytes(b[0]),bytes(b[1]),b[2:]);checks+=1
first=current.mask_buffer_types(2,3);a=first[1](1,0,1);b=first[1](1,0,1);a[0]=0;assert b[0]==1
for i in range(96):current.mask_buffer_types(1,i)
assert current.mask_buffer_types.cache_info().currsize==64
for dimensions in ((0,1),(146,1),(1,-1),(1,32769)):
 try:current.mask_buffer_types(*dimensions)
 except ValueError:pass
 else:raise AssertionError('Invalid buffer dimensions accepted')
result=dict(result='PASS_BASELINE_MASK_BYTES_PRIVATE_BUFFERS_BOUNDED_TYPES',baseline_cases=checks,cache_bound=64,invalid_dimensions_rejected=4,scope='Synthetic mask packing baseline parity, private instances and bounded class cache; actual complete-scene replay tested separately.')
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/face-mask-type-audit-20261007');(cp/'mask-type-parity.json').write_text(json.dumps(result,indent=2));print(result)
