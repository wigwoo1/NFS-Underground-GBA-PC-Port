import ctypes as C,json,struct,statistics
from pathlib import Path
p=Path('work/camera');d=C.CDLL(str((p/'owned-hud-creation-profile-candidate.dll').resolve()));U=C.c_uint64;P=C.c_void_p
d.nf_hud_owner_create.argtypes=[P,C.c_size_t,U,C.c_uint];d.nf_hud_owner_create.restype=U;d.nf_hud_owner_release.argtypes=[U,U];d.nf_hud_owner_stats.argtypes=[P];d.nf_hud_owner_creation_profile.argtypes=[P]
r=json.loads((p/'prototype-runs/owned-native-1791434872973979000.json').read_text());folder=Path(r['live_preparation_profiles'][0]['capture']);frames=[(folder/name).read_bytes() for name in ('older.frame.bin','newer.frame.bin')]
inputs=[]
for f in frames:
 h=struct.unpack_from('<6I2Q',f);assert h[3]==5591040
 inputs.append((C.c_char_p(f),40+h[2],h[6],h[1]))
held=[];rows=[];profile=(U*10)()
try:
 for i in range(102):
  if len(held)>=2:
   token,epoch=held.pop(0);assert d.nf_hud_owner_release(token,epoch)
  owner,offset,epoch,refresh=inputs[i%2];token=d.nf_hud_owner_create(C.cast(owner,P).value+offset,5591040,epoch,refresh);assert token;held.append((token,epoch))
  assert d.nf_hud_owner_creation_profile(profile);rows.append(list(profile))
finally:
 for token,epoch in held:assert d.nf_hud_owner_release(token,epoch)
stats=(U*3)();assert d.nf_hud_owner_stats(stats) and list(stats)==[0,0,0]
names=['row_validation','registry_lock','allocation_and_slot_search','copy','publish_unlock']
def summary(group):return {name:dict(median_ms=statistics.median(row[i]/1e6 for row in group),median_cycles=statistics.median(row[i+5] for row in group)) for i,name in enumerate(names)}
out=dict(result='HUD_CREATE_NATIVE_STAGE_PROFILE',first_two=summary(rows[:2]),warm_rotation=summary(rows[2:]),records=rows,final_stats=list(stats),scope='Two actual captured immutable frames, 102 two-owner rotating creations. Standalone warm memory/allocator component; no live cost or matched optimization benefit. Execution cycles not converted to elapsed time.')
(p/'prototype-runs/hud-create-stage-profile-20261009.json').write_text(json.dumps(out,indent=2));print(out['result'],out['first_two'],out['warm_rotation'])
