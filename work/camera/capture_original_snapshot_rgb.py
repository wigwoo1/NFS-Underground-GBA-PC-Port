from pathlib import Path
import ctypes as C,json,hashlib
from scene_batches import records
p=Path('work/camera');f=C.CDLL(str((p/'sprite_original_oracle.dll').resolve())).nfs_original_snapshot_rgb;f.argtypes=[C.c_void_p]*6
assets=p/'motion-static-rgb-assets';assets.mkdir(exist_ok=True);checks=[]
for e in records(p/'motion-original-video-state-world.bin'):
 if e['pc']!=0x04000000 or not 8757<=e['frame']<=8779:continue
 out=(C.c_uint32*38400)();palette=e['blocks'][67][1]+e['blocks'][100][1]
 assert f(e['blocks'][92][1],e['blocks'][98][1],e['blocks'][99][1],palette,e['blocks'][103][1],out)
 data=bytes(out);target=assets/f"{e['frame']}-rgb.bin";target.write_bytes(data)
 checks.append(dict(refresh=e['frame'],rgb_path=str(target),sha256=hashlib.sha256(data).hexdigest(),unique_colors=len(set(out))))
assert len(checks)==7
report=dict(result='RENDERED_ORIGINAL_STATIC_SNAPSHOT_RGB',checks=checks,scope='Original mgba software renderer static snapshot replay from captured page/OBJ/OAM/palettes/video IO. No actual emulator scanline-history or native RGB parity claim.')
(p/'original-static-snapshot-rgb-tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(report)
