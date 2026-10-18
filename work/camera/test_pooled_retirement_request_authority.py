import ctypes as C,struct,json
from pathlib import Path
P=C.c_void_p;U=C.c_uint64;Z=C.c_size_t
d=C.CDLL(str(Path('work/camera/owned-handoff-request-retirement-candidate.dll').resolve()))
for name,args,result in [('create',[U],P),('request_generation',[P,U,P],C.c_int),('push_authority',[P,P,Z,U,U,P],C.c_int),('pop_token',[P,P,P],P),('pause',[P,C.c_uint],C.c_int),('epoch',[P,U],C.c_int),('pool_stats',[P,P],C.c_int),('close',[P],None),('destroy',[P],None)]:
 f=getattr(d,'nf_owned_handoff_'+name);f.argtypes=args;f.restype=result
d.nf_owned_frame_free.argtypes=[P]
raw=Path('work/camera/motion-actual-scanline-assets/8758-native-complete-frame.bin').read_bytes();epoch=struct.unpack_from('<Q',raw,24)[0];q=d.nf_owned_handoff_create(epoch);assert q
try:
 g=U();assert d.nf_owned_handoff_request_generation(q,epoch,C.byref(g));old=g.value
 assert d.nf_owned_handoff_pause(q,1);sentinel=U(123);assert not d.nf_owned_handoff_request_generation(q,epoch,C.byref(sentinel));assert sentinel.value==123
 assert d.nf_owned_handoff_pause(q,0)
 assert not d.nf_owned_handoff_push_authority(q,raw,len(raw),epoch,old,(U*8)())
 stats=(U*4)();assert d.nf_owned_handoff_pool_stats(q,stats);assert stats[0]==0,'Retired request copied before rejection'
 assert d.nf_owned_handoff_request_generation(q,epoch,C.byref(g));assert g.value!=old
 assert d.nf_owned_handoff_push_authority(q,raw,len(raw),epoch,g.value,(U*8)())
 size=Z();token=U();p=d.nf_owned_handoff_pop_token(q,C.byref(size),C.byref(token));assert p and token.value==g.value and C.string_at(p,size.value)==raw
 assert d.nf_owned_handoff_epoch(q,epoch+1);assert C.string_at(p,size.value)==raw;d.nf_owned_frame_free(p)
 assert not d.nf_owned_handoff_push_authority(q,raw,len(raw),epoch,g.value,(U*8)())
 assert not d.nf_owned_handoff_push_authority(q,raw,len(raw),epoch+1,g.value,(U*8)())
 d.nf_owned_handoff_close(q);assert not d.nf_owned_handoff_request_generation(q,epoch+1,C.byref(g))
finally:d.nf_owned_handoff_destroy(q)
Path('work/camera/prototype-runs/pooled-retirement-request-authority-20261010.json').write_text(json.dumps(dict(library=d._name,result='PASS_REQUEST_AUTHORITY_REJECTS_RETIRED_BEFORE_COPY',actual_frame_bytes=len(raw),scope='Native component, no background service/live timing integration.'),indent=2));print('PASS_REQUEST_AUTHORITY_REJECTS_RETIRED_BEFORE_COPY')

