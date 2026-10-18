"""Joined world source -> retained raw matrix -> original-compatible projection."""
from pathlib import Path
import json,ctypes as C
p=Path('work/camera');events=json.loads((p/'stable-original-road-source.json').read_text())['roads'];geo=json.loads((p/'stable-road-geometric-inputs.json').read_text());joins=json.loads((p/'stable-road-source-transform-comparison.json').read_text())['checks']
camera=C.CDLL(str((p/'road-camera-continuous.dll').resolve())).nf_road_camera_continuous;camera.argtypes=[C.c_void_p]*3
import struct
matrices={e['source']:struct.unpack('<12i',bytes.fromhex(e['blocks']['2']['hex'])) for e in events}
computed={}
for j in joins:
 g=next(g for g in geo['roads'] if g['surface']==j['surface']);m=(C.c_int32*12)(*matrices[j['source']])
 for k,v in enumerate(g['vertices']):
  out=(C.c_double*3)();assert camera((C.c_double*3)(*v),m,out);computed[(j['source'],k)]=list(out)
s=(p/'test_road_point_project_continuous.py').read_text();s=s.replace("point=j['vertices'][index]['original_camera']","point=computed[(m['source'],index)]")
s=s.replace("road-point-project-continuous-tests.json","road-world-camera-project-tests.json")
s=s.replace('Retained source-corner projection/UV matches original stream by source identity, no screen matching. Near-generated positions/camera Q14 transform/native integration/GPU/fullmotion unverified.','Joined native world vertices and original raw matrix through camera component and projection exactly match retained source corners. Near-generated positions, packet integration, GPU and full motion remain unverified.')
exec(compile(s,'combined_source_pipeline','exec'),globals())
