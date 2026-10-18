import ctypes as C,json,threading
from pathlib import Path
from live_native_batch_candidate import NativeBatchWorker
from owned_active_batch_publication import ActiveBatchPublication
P=C.c_void_p
lib=C.CDLL(str(Path('work/camera/owned-batch-present-candidate.dll').resolve()))
lib.nf_owned_handoff_create.argtypes=[C.c_uint64];lib.nf_owned_handoff_create.restype=P
lib.nf_owned_handoff_pause.argtypes=[P,C.c_uint];lib.nf_owned_handoff_destroy.argtypes=[P]
registration=C.PyDLL(str(Path('work/camera/owned-batch-present-candidate.dll').resolve()));registration.nf_owned_handoff_commit_token.argtypes=[P,C.c_uint64,C.c_uint64,C.CFUNCTYPE(C.c_int,P),P]
w=NativeBatchWorker.__new__(NativeBatchWorker);w.d=lib;w.registration_bridge=registration;w.owner=lib.nf_owned_handoff_create(7);w.batch_publication=ActiveBatchPublication()
rows=[dict(epoch=7,generation=1,source_older=10,refresh=14,display_index=20,alpha=.25)]
try:
 assert lib.nf_owned_handoff_pause(w.owner,1)
 assert w.register_native_batch(7,1,rows,object()) is None and w.batch_publication.active is None
 assert lib.nf_owned_handoff_pause(w.owner,0)
 assert w.register_native_batch(7,1,rows,object()) is None and w.batch_publication.active is None
 rows[0]['generation']=3
 token=w.register_native_batch(7,3,rows,object());assert token is not None and w.batch_publication.active
 assert lib.nf_owned_handoff_pause(w.owner,1)
 assert w.batch_publication.finish(token,[])==() and w.batch_publication.active is None
finally:lib.nf_owned_handoff_destroy(w.owner)
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-batch-registration-retirement-20261007');cp.mkdir(parents=True,exist_ok=True)
(cp/'tests.json').write_text(json.dumps(dict(result='PASS',checks=['paused token rejected without owner publication','retired resumed token rejected','current generation accepted','post-registration pause empty prefix releases owner'],scope='Actual native lifecycle with Python registry; stand-in frame owner, not GPU or concurrent full-game race proof'),indent=2))
print('PASS native batch registration retirement')
