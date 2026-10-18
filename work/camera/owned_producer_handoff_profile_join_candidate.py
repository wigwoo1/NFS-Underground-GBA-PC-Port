"""Read producer-thread TLS handoff profile at submission record publication."""
import ctypes as C,threading
from pathlib import Path
from owned_producer_submission_join_candidate import ProducerRows,SubmissionRows as Base
_d=C.CDLL(str(Path('work/camera/owned-handoff-copy-profile-candidate.dll').resolve()))
_d.nf_owned_handoff_copy_profile.argtypes=[C.c_void_p];_d.nf_owned_handoff_copy_profile.restype=C.c_int
class SubmissionRows(Base):
 def append(self,row):
  assert row['thread_id']==threading.get_ident()
  profile=(C.c_uint64*3)();assert _d.nf_owned_handoff_copy_profile(profile) and profile[2]>0
  joined=dict(row);joined['handoff_allocate_ns']=profile[0]*1000000000//profile[2];joined['handoff_memcpy_ns']=profile[1]*1000000000//profile[2]
  assert joined['handoff_allocate_ns']+joined['handoff_memcpy_ns']<=row['native_copy_unlocked_ns']+200
  super().append(joined)
