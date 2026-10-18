import ctypes as C,json,struct,threading
from pathlib import Path
p=Path('work/camera');d=C.CDLL(str((p/'owned-hud-creation-profile-candidate.dll').resolve()));U=C.c_uint64;P=C.c_void_p
d.nf_hud_owner_create.argtypes=[P,C.c_size_t,U,C.c_uint];d.nf_hud_owner_create.restype=U;d.nf_hud_owner_view.argtypes=[U,U,P,P];d.nf_hud_owner_release.argtypes=[U,U];d.nf_hud_owner_stats.argtypes=[P]
r=json.loads((p/'prototype-runs/owned-native-1791434872973979000.json').read_text());f=(Path(r['live_preparation_profiles'][0]['capture'])/'older.frame.bin').read_bytes();refresh,gn,hn=struct.unpack_from('<III',f,4);epoch=struct.unpack_from('<Q',f,24)[0];hud=f[40+gn:40+gn+hn];assert hn==5591040
src=C.create_string_buffer(hud);tokens=[]
def stats():
 a=(U*3)();assert d.nf_hud_owner_stats(a);return list(a)
def view(token,e=epoch):
 ptr=P();r=C.c_uint();result=d.nf_hud_owner_view(token,e,C.byref(ptr),C.byref(r));return result,ptr.value,r.value
try:
 assert stats()==[0,0,0]
 bad=C.create_string_buffer(hud);C.c_uint32.from_buffer(bad,159*34944+4).value=158;assert d.nf_hud_owner_create(bad,hn,epoch,refresh)==0 and stats()==[0,0,0]
 assert d.nf_hud_owner_create(src,hn-1,epoch,refresh)==0;assert d.nf_hud_owner_create(src,hn,0,refresh)==0
 for _ in range(8):
  token=d.nf_hud_owner_create(src,hn,epoch,refresh);assert token;tokens.append(token)
 assert len(set(tokens))==8 and stats()==[8,8*hn,8];assert d.nf_hud_owner_create(src,hn,epoch,refresh)==0
 token=tokens[0];assert view(token,epoch+1)[0]==0;assert d.nf_hud_owner_release(token,epoch+1)==0
 acquired=threading.Event();release=threading.Event();errors=[]
 def reader():
  try:
   ok,ptr,r=view(token);assert ok and r==refresh;acquired.set();assert release.wait(5);assert C.string_at(ptr,hn)==hud;assert d.nf_hud_owner_release(token,epoch)
  except BaseException as error:errors.append(repr(error));acquired.set()
 t=threading.Thread(target=reader);t.start();assert acquired.wait(5);assert not errors
 C.c_uint8.from_buffer(src,100).value^=255
 assert d.nf_hud_owner_release(token,epoch);tokens.remove(token);release.set();t.join(5);assert not t.is_alive() and not errors,errors
 assert view(token)[0]==0 and d.nf_hud_owner_release(token,epoch)==0
 replacement=d.nf_hud_owner_create(C.create_string_buffer(hud),hn,epoch,refresh);assert replacement and replacement!=token;tokens.append(replacement);assert view(token)[0]==0
finally:
 if 'release' in globals():release.set()
 if 't' in globals():t.join(5)
 for token in tokens:assert d.nf_hud_owner_release(token,epoch)
assert stats()==[0,0,0]
out=dict(result='PASS_NATIVE_HUD_OWNERSHIP_LEASE_LIFETIME',source_bytes=hn,slot_limit=8,budget_bytes=8*hn,capacity_rejected=True,late_row_header_rejected=True,source_mutation_isolated=True,reader_survives_creator_release=True,stale_token_rejected_after_reuse=True,wrong_epoch_rejected=True,final_stats=stats(),scope='Actual capturedHUD bytes and forced reader/creator release barrier. Native component only; not integrated with renderer/pause/frame pairing or gameplay timing.')
(p/'prototype-runs/native-hud-profile-owner-20261009.json').write_text(json.dumps(out,indent=2));print(out)
