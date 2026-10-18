"""Force actual private-reader row rejection after partial native assembly."""
import ctypes as C,runpy,json
from pathlib import Path
import _owned_frame_capture_profile_candidate as extension
original=extension.capture
library=C.CDLL(str(Path('work/camera/viewport-sky-private-failure-test.dll').resolve()))
private=library.nf_native_owned_frame_read_private;legacy=library.nf_native_owned_frame_read
for f in (private,legacy):f.argtypes=[C.c_uint64,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)];f.restype=C.c_int
hook=library.nf_private_test_fail_row;hook.argtypes=[C.c_int];hook.restype=C.c_int
count=0;checks=[]
def capture(address,epoch,refresh):
 global count
 count+=1
 if count==40:
  size=C.c_size_t();assert private(epoch,refresh,None,0,C.byref(size))==1
  reference=C.create_string_buffer(size.value);assert legacy(epoch,refresh,reference,size.value,C.byref(size))==1
  for row in (0,159):
   assert hook(row)==1
   try:
    output=C.create_string_buffer(b'X'*size.value);written=C.c_size_t(123)
    assert private(epoch,refresh,output,size.value,C.byref(written))==0 and written.value==123
    assert output.raw[:40]!=b'X'*40,'No partial assembly exercised'
    try:original(address,epoch,refresh)
    except ValueError as error:assert 'capture failed' in str(error)
    else:raise AssertionError('Partial frame escaped')
    check=C.create_string_buffer(size.value);assert legacy(epoch,refresh,check,size.value,C.byref(written))==1 and check.raw==reference.raw
   finally:assert hook(-1)==1
   assert original(address,epoch,refresh)==reference.raw
   checks.append(dict(row=row,partial_native_output=True,written_unpublished=True,extension_discarded=True,legacy_unaffected=True,recovery_byteexact=True))
 return original(address,epoch,refresh)
extension.capture=capture
try:
 runpy.run_path('work/camera/run_native_private_failure_test.py',run_name='__main__')
 assert len(checks)==2
 out=dict(result='PASS_ACTUAL_PRIVATE_READER_ROW_FAILURE_DISCARD_RECOVERY',checks=checks,captures=count,scope='Test-only native early/late row gate rejection with actual captured source state. Private partial output is discarded by extension; legacy stays atomic. Timing perturbed, no cadence qualification.')
 Path('work/camera/prototype-runs/private-native-row-failure-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'])
finally:extension.capture=original;assert hook(-1)==1
