import ctypes as C,struct,json
from pathlib import Path
p=Path('work/camera');d=C.CDLL(str((p/'hud-visual-equal-component.dll').resolve()));d.nf_test_hud_equal.argtypes=[C.c_void_p,C.c_void_p,C.c_uint32];size=d.nf_test_hud_row_size();assert size==34944
base=bytearray(size*160)
for y in range(160):struct.pack_into('<II',base,y*size,100,y)
def equal(a,b,refresh):return d.nf_test_hud_equal(C.create_string_buffer(bytes(a)),C.create_string_buffer(bytes(b)),refresh)
checks=[]
for refresh in (100,101,200,0xffffffff):
 b=bytearray(base)
 for y in range(160):struct.pack_into('<I',b,y*size,refresh)
 assert equal(base,b,refresh)==1;checks.append(dict(case='identical_visual_new_refresh',refresh=refresh))
for y in (0,79,159):
 for offset in (8,103,104,127,128,32895,32896,33919,33920,34943):
  b=bytearray(base);b[y*size+offset]^=1;assert equal(base,b,100)==0;checks.append(dict(case='visual_byte_changed',row=y,offset=offset))
 for offset in (0,4):
  b=bytearray(base);b[y*size+offset]^=1;assert equal(base,b,100)==0;checks.append(dict(case='current_identity_invalid',row=y,offset=offset))
 a=bytearray(base);a[y*size+4]^=1;assert equal(a,base,100)==0;checks.append(dict(case='cached_row_invalid',row=y))
assert equal(base,base,101)==0
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/4k-hud-visual-reuse-20261008');out=dict(result='PASS',row_size=size,checks=checks,scope='Exact generated native comparison function, synthetic complete160rows. Refresh-only changes accepted; content/row/currentrefresh mutations rejected. Epoch/text gates remain outside this component; no fullscene crossrefresh or live performance proof.')
(cp/'comparison-component.json').write_text(json.dumps(out,indent=2));print('PASS',len(checks)+1,'native cases')
