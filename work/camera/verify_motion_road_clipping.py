from pathlib import Path
import json,struct,ctypes as C
p=Path('work/camera');capture=json.loads((p/'motion-original-road-source-intervals.json').read_text());poses={(v['begin'],v['source']):v for v in json.loads((p/'motion-road-source-endpoints.json').read_text())['checks']};clip=C.CDLL(str((p/'road-clip-continuous.dll').resolve())).nf_road_clip_continuous;clip.argtypes=[C.c_void_p,C.c_uint,C.c_double,C.c_double,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());checks=[]
for scene in capture['scenes']:
 for road in scene['roads']:
  key=(scene['begin'],road['source'])
  if key not in poses:continue
  pose=poses[key];ring=[[v[0],v[1],v[1],v[2],v[3],v[4]] for v in pose['actual']];blocks={int(k):bytes.fromhex(v['hex']) for k,v in road['blocks'].items()};bd=struct.unpack_from('<4H',blocks[1],226);first,count=struct.unpack_from('<2H',blocks[1],242);expected=[list(struct.unpack_from('<6i',blocks[7],(first+j)*24)) for j in range(count)];expected=[[v[k] for k in (0,1,3,4,5)] for v in expected]
  data=(C.c_double*(len(ring)*6))(*(v for row in ring for v in row));out=(C.c_double*768)();n=C.c_uint();assert clip(data,len(ring),bd[0],bd[1],table,out,128,C.byref(n));actual=[[out[j*6+k] for k in (0,1,3,4,5)] for j in range(n.value)]
  checks.append(dict(begin=scene['begin'],source=road['source'],command=pose['command'],bounds=list(bd),actual=actual,expected=expected,exact=actual==expected))
r=dict(result='PASS_ACTUAL_CLIPPED_ENDPOINTS' if all(v['exact'] for v in checks) else 'CLIPPED_ENDPOINT_MISMATCH',checks=checks,draws=len(checks),vertices=sum(len(v['actual']) for v in checks),scope='Five rendered fields/sourceorder at21knownroad original draw endpoints withactual perdraw bounds; unused field not compared. No otherdraw/fullscene or betweenpose visibility proof.')
(p/'motion-road-clipped-endpoints.json').write_text(json.dumps(r,indent=2));print(r['result'],r['draws'],r['vertices']);print([dict(begin=v['begin'],command=v['command'],bounds=v['bounds'],actual=v['actual'],expected=v['expected']) for v in checks if not v['exact']][:2])
