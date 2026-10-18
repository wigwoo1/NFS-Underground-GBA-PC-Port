"""Borrowed immutable input versus native copy before unchanged sky attachment."""
import ctypes as C,json
from pathlib import Path
source=Path('work/camera/test_owned_sky_frame.py').read_text().split("cp=Path(")[0]
exec(compile(source,'sky_fixture','exec'))
checks=[]
for name,value in [('original',original),('attached',result)]+[(f'invalid-{i}',bytes(v)) for i,v in enumerate(cases)]:
 outcomes=[]
 native=C.create_string_buffer(value)
 for item in (value,C.string_at(native,len(value))):
  try:outcomes.append(('ok',attach_sky(item,scene)))
  except ValueError as e:outcomes.append(('error',str(e)))
 assert outcomes[0]==outcomes[1]
 checks.append(dict(case=name,outcome=outcomes[0][0]))
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/owned-sky-attachment-live-20261008')
(cp/'input-equivalence.json').write_text(json.dumps(dict(result='PASS',checks=checks,scope='Archived sky/frame fixture; borrowed bytes versus copied native bytes produce exact attachment or identical validation errors. Not fresh fullscene pixel proof.'),indent=2));print('PASS',len(checks),'attachment input equivalence cases')
