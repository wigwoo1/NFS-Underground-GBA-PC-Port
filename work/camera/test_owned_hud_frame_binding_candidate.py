import ctypes as C,json,struct
from pathlib import Path
from owned_hud_frame_binding_candidate import HudFrameSnapshot
from owned_segmented_frame_candidate import SegmentedFrame
p=Path('work/camera');r=json.loads((p/'prototype-runs/owned-native-1791434872973979000.json').read_text());folder=Path(r['live_preparation_profiles'][0]['capture']);base=(folder/'older.frame.bin').read_bytes();offset=40+struct.unpack_from('<I',base,8)[0];frame=SegmentedFrame(base[:offset],base,offset)
owner=HudFrameSnapshot(base);leases=[]
try:
 for _ in range(5):leases.append(owner.bind(frame))
 assert len({x.pointer for x in leases})==1
 bad=bytearray(base);bad[offset+100]^=1;different=bytes(bad);wrong=SegmentedFrame(different[:offset],different,offset)
 try:owner.bind(wrong)
 except ValueError:pass
 else:raise AssertionError('Wrong immutable source accepted')
 owner.close()
 try:owner.bind(frame)
 except ValueError:pass
 else:raise AssertionError('Closed snapshot accepted')
 expected=base[offset:offset+5591040]
 for lease in leases:assert C.string_at(lease.pointer,5591040)==expected
finally:
 owner.close()
 for lease in leases:lease.close()
stats=(C.c_uint64*3)();assert owner.d.nf_hud_owner_stats(stats) and list(stats)==[0,0,0]
try:leases[0].pointer
except ValueError:pass
else:raise AssertionError('Closed lease view accepted')
out=dict(result='PASS_IMMUTABLE_SEGMENTED_FRAME_HUD_ASSOCIATION',leases=5,wrong_frame_same_envelope_rejected=True,reader_survives_snapshot_close=True,closed_lease_rejected=True,final_stats=list(stats),scope='Validated actual captured immutable frame, native exact copy and lease association. No renderer ABI/cache skip/pause integration or timing proof.')
(p/'prototype-runs/hud-frame-binding-20261009.json').write_text(json.dumps(out,indent=2));print(out)
