from pathlib import Path
import ctypes as C,json,struct
from scene_batches import records
p=Path('work/camera');events={e['id']:e for e in records(p/'motion-original-source-8750-8781.bin')};snap=json.loads((p/'motion-wall-snapshots.json').read_text());camera=C.CDLL(str((p/'road-camera-continuous.dll').resolve())).nf_road_camera_continuous;camera.argtypes=[C.c_void_p]*3;project=C.CDLL(str((p/'road-point-project-continuous.dll').resolve())).nf_road_point_project_continuous;project.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint]+[C.c_void_p]*3;table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());checks=[];order=C.CDLL(str((p/'wall-edge-order.dll').resolve())).nf_wall_edge_order;order.argtypes=[C.c_int,C.c_int,C.c_uint,C.c_void_p]
for scene in snap['scenes']:
 for wall in scene['walls']:
  e=events[wall['event']];edge=e['blocks'][6][1];half=struct.unpack('<26h',edge);flags=struct.unpack_from('<H',edge,48)[0];actual=[];expected=[];skipped=[]
  for ordinal,vertex in enumerate(wall['world_vertices']):
   side=0 if ordinal in (0,3) else 1
   if flags&(8 if side==0 else 16):skipped.append(ordinal);continue
   point=(C.c_double*3)();assert camera((C.c_double*3)(*vertex),bytes.fromhex(wall['camera_hex']),point);out=(C.c_double*5)();assert project(point,(C.c_int32*2)(0,0),8,128,(C.c_int32*3)(120,87,128),table,out)
   actual.append([out[0],out[1],point[2]]);expected.append([half[side],half[4+side] if ordinal<2 else half[6+side],half[2+side]&65535])
  if len(actual)==4:
   ordered=(C.c_int*3)();assert order(int(actual[0][0]),int(actual[1][0]),wall['flags'],ordered)
   for ordinal in range(4):actual[ordinal][0]=ordered[0 if ordinal in (0,3) else 1]
  checks.append(dict(event=wall['event'],source=wall['source'],edge=wall['edge'],actual=actual,expected=expected,skipped_clipped_vertices=skipped,exact=actual==expected))
r=dict(result='PASS_UNCUT_WALL_WORLD_PROJECTION' if all(v['exact'] for v in checks) else 'WALL_WORLD_PROJECTION_DIFFERENCE',checks=checks,scope='Native worldquad camera/point projection vs original prepared X/Y/cameraZ at uncutwall endpoints after original sourceflag horizontal ordering. Nearclipped endpoint interpolation/UV/columnstate not verified; clipped endpoints explicitskips.')
(p/'motion-wall-projection-tests.json').write_text(json.dumps(r,indent=2));print(r['result'],len(checks));print([v for v in checks if not v['exact']][:2])
