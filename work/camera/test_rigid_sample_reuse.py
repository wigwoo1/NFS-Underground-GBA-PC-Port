from pathlib import Path
from unittest.mock import patch
import sample_owned_motion as motion
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0]
exec(compile(source,'captured_scene_setup','exec'))
m=prepared.pair.portal.motion;m._sample_cache.clear()
try:
 with patch.object(motion,'_sample_prepared',wraps=motion._sample_prepared) as measured:
  a=m.sample(.5);b=m.sample(.5)
  assert measured.call_count==1 and a[0]==b[0] and bytes(a[1])==bytes(b[1]) and bytes(a[2])==bytes(b[2])
  assert a[1] is not b[1] and a[2] is not b[2]
  a[1][0]=999;a[2][0]=999
  c=m.sample(.5);assert bytes(b[1])==bytes(c[1]) and bytes(b[2])==bytes(c[2])
  for alpha in (.1,.2,.3,.4,.6,.7,.8,.9):m.sample(alpha)
  assert len(m._sample_cache)==8 and .5 not in m._sample_cache
  old_count=measured.call_count;m.sample(.5);assert measured.call_count==old_count+1
 for alpha in (0,1,.25,.75):
  a=m.sample(alpha);b=motion._sample_prepared(m.older,m.newer,alpha,*m.arguments)
  assert a[0]==b[0]
  if a[1] is not None:assert bytes(a[1])==bytes(b[1]) and bytes(a[2])==bytes(b[2])
 for alpha in (-1,float('nan'),2):
  try:m.sample(alpha);raise AssertionError('Invalid alpha accepted')
  except ValueError:pass
 print('PASS: native rigid evaluation once per alpha, private mutable outputs, exact uncached parity, bounded8 eviction, invalid alpha rejection')
finally:prepared.close();history.close()
