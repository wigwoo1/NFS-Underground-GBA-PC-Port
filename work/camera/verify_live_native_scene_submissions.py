from pathlib import Path
import struct,collections,json
p=Path('work/camera');raw=(p/'motion-live-native-model-plans.bin.scene.bin').read_bytes();assert len(raw)%20==0
records=[struct.unpack_from('<5I',raw,o) for o in range(0,len(raw),20)]
assert all(r[0] in (0x3153534e,0x3143534e) for r in records)
sub=[r for r in records if r[0]==0x3153534e];checks=[r for r in records if r[0]==0x3143534e]
assert sub and checks and all(r[3] for r in sub) and all(r[3] and r[4]==0 for r in checks)
assert set(r[2] for r in sub)==set(range(1,7))
r=dict(result='PASS_LIVE_INPROCESS_PERSISTENT_SCENE',submissions=len(sub),draw_checks=len(checks),exact_draw_checks=len(checks),comparison_bytes=len(checks)*0x18000,submissions_by_kind=dict(collections.Counter(r[2] for r in sub)),scope='One seed at first resolved road. In-process synchronous retained native road/wall/model/fill/copy execution vs original complete VRAM at draw return. Diagnostic original renderer remains active; not native4K or60fps gameplay proof.')
(p/'live-native-scene-submission-tests.json').write_text(json.dumps(r,indent=2));print(r)
