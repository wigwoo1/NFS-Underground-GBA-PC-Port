import ctypes as C,struct,json,threading
from pathlib import Path
d=C.CDLL(str(Path('work/camera/owned-hud-snapshot-short-lock-candidate.dll').resolve()))
U=C.c_uint64;P=C.c_void_p
d.nf_hud_owner_create.argtypes=[P,C.c_size_t,U,C.c_uint];d.nf_hud_owner_create.restype=U
d.nf_hud_owner_view.argtypes=[U,U,C.POINTER(P),C.POINTER(C.c_uint)]
d.nf_hud_owner_release.argtypes=[U,U]
d.nf_hud_owner_stats.argtypes=[C.POINTER(U)]
size=160*34944
raw=bytearray(size)
for y in range(160):struct.pack_into('<2I',raw,y*34944,123,y)
data=C.create_string_buffer(bytes(raw));tokens=[]
for _ in range(8):
 t=d.nf_hud_owner_create(data,size,9,123);assert t;tokens.append(t)
assert not d.nf_hud_owner_create(data,size,9,123)
pointer=P(1234);refresh=C.c_uint(5678)
assert not d.nf_hud_owner_view(tokens[0],10,C.byref(pointer),C.byref(refresh))
assert pointer.value==1234 and refresh.value==5678
assert not d.nf_hud_owner_release(tokens[0],10)
assert d.nf_hud_owner_view(tokens[0],9,C.byref(pointer),C.byref(refresh))
assert refresh.value==123 and C.string_at(pointer,size)==bytes(raw)
assert d.nf_hud_owner_release(tokens[0],9)
assert C.string_at(pointer,size)==bytes(raw) # live acquired lease survives creator retirement
assert d.nf_hud_owner_release(tokens[0],9)
assert not d.nf_hud_owner_release(tokens[0],9)
for t in tokens[1:]:assert d.nf_hud_owner_release(t,9)
errors=[]
def exercise():
 try:
  for _ in range(32):
   t=d.nf_hud_owner_create(data,size,9,123);assert t
   ptr=P();r=C.c_uint();assert d.nf_hud_owner_view(t,9,C.byref(ptr),C.byref(r))
   assert d.nf_hud_owner_release(t,9)
   assert C.string_at(ptr,8)==struct.pack('<2I',123,0)
   assert d.nf_hud_owner_release(t,9)
 except BaseException as e:errors.append(repr(e))
threads=[threading.Thread(target=exercise) for _ in range(2)]
for t in threads:t.start()
for t in threads:t.join()
assert not errors,errors
stats=(U*3)();assert d.nf_hud_owner_stats(stats) and list(stats)==[0,0,0]
out=dict(result='PASS_SHORT_LOCK_OWNER_LEASE_COMPONENT',concurrent_cycles=64,capacity=8,private_payload_exact=True,wrong_epoch_output_unchanged=True,lease_survives_creator_release=True,stale_release_rejected=True,final_stats=list(stats),scope='Standalone native owner component; no live renderer/4K/timing gain qualification.')
Path('work/camera/prototype-runs/hud-short-lock-owner-20261009.json').write_text(json.dumps(out,indent=2));print(out)
