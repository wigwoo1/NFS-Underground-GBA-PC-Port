from pathlib import Path
import zlib,json,numpy as np
p=Path('work/camera/prototype-runs');rows=[]
def read(n):return np.frombuffer(zlib.decompress((p/n).read_bytes()),np.uint8).reshape(2160,3840,3)
for i in range(5):
 world=np.any(read(f'gl-source-world-{i}.rgb.z')!=read(f'd3d-matrix_load-world-{i}.rgb.z'),axis=2)
 full=np.any(read(f'gl-source-full-{i}.rgb.z')!=read(f'd3d-full-scene-{i}.rgb.z'),axis=2)
 new=int((full&~world).sum());assert new==0
 rows.append(dict(frame=i,full_differences=int(full.sum()),new_difference_locations=new))
(p/'d3d-full-scene-hud-localization.json').write_text(json.dumps(dict(result='PASS_NO_NEW_HUD_DIFFERENCE_LOCATIONS',frames=rows,scope='Five fixture frames only; residual world mismatches remain, not full exact parity or general HUD proof.'),indent=2));print(rows)
