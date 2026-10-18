from pathlib import Path
import json,struct,ctypes as C
from scene_batches import records
p=Path('work/camera');capture=json.loads((p/'motion-original-road-source-intervals.json').read_text());geo=json.loads((p/'stable-road-geometric-inputs.json').read_text());joins={j['source']:j for j in json.loads((p/'stable-road-source-transform-comparison.json').read_text())['checks']};events=list(records(p/'motion-original-source-8750-8781.bin'));table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());source=C.CDLL(str((p/'road-source-ring-motion-audit.dll').resolve())).nf_road_source_ring;source.argtypes=[C.c_void_p,C.c_uint]+[C.c_void_p]*5+[C.c_uint,C.c_void_p];checks=[];unknown=[]
i=lambda b,o:struct.unpack_from('<i',b,o)[0];h=lambda b,o:struct.unpack_from('<h',b,o)[0]
for scene in capture['scenes']:
 for road in scene['roads']:
  if road['source'] not in joins:unknown.append(dict(begin=scene['begin'],source=road['source']));continue
  join=joins[road['source']];g=next(v for v in geo['roads'] if v['surface']==join['surface']);blocks={int(k):bytes.fromhex(v['hex']) for k,v in road['blocks'].items()};count=struct.unpack_from('<H',blocks[4],2)[0];face=blocks[42] or bytes(20);world=[];attrs=[]
  for j in range(count):
   v=blocks[5][j*68:(j+1)*68];off=blocks[10+j] or bytes(32);world.append([i(v,0)+h(off,0),h(v,56)+h(off,6)+h(face,6),i(v,4)+h(off,2)]);attrs.append([i(v,32),i(v,36)])
  assert world==g['vertices'] and attrs==g['source_attributes'],(scene['begin'],road['source'],'geometry changed')
  raw=struct.pack('<6I66i',*g['source_attributes_header'],*(v for pair in attrs for v in pair),*([0]*(64-count*2)));matrix=blocks[2];out=(C.c_double*320)();n=C.c_uint();assert source((C.c_double*(count*3))(*(v for r in world for v in r)),count,raw,matrix,(C.c_int32*3)(120,87,128),table,out,64,C.byref(n))
  before=max((e for e in events if e['id']<road['event'] and e['pc']==0x03001800 and e['blocks'][4][0]==road['source']),key=lambda e:e['id']);after=min((e for e in events if before['id']<e['id']<road['event'] and e['pc']==0x03002964 and e['blocks'][4][0]==road['source']),key=lambda e:e['id']);emitted=struct.unpack_from('<H',after['blocks'][1][1],242)[0];expected=[list(struct.unpack_from('<6i',after['blocks'][7][1],j*24)) for j in range(emitted)];expected=[[r[k] for k in (0,1,3,4,5)] for r in expected];actual=[list(out[j*5:j*5+5]) for j in range(n.value)]
  checks.append(dict(begin=scene['begin'],end=scene['end'],source=road['source'],command=join['command'],matrix_hex=matrix.hex(),world=world,attributes_header=g['source_attributes_header'],attributes=attrs,actual=actual,expected=expected,exact=actual==expected));print(scene['begin'],join['command'],'exact',actual==expected,flush=True)
report=dict(result='PASS_KNOWN_ROAD_ENDPOINTS' if all(c['exact'] for c in checks) else 'FAIL_ENDPOINTS',checks=checks,unassociated_draws=unknown,scope='Actual source/world/rawUV identity from original draw records and exact emitted source stream endpoint parity across7completegame scenes for3knownroads. Other10draws notyetassociated; no poseinterpolation/fullscene proof.')
(p/'motion-road-source-endpoints.json').write_text(json.dumps(report,indent=2));print(report['result'],len(checks),len(unknown))
