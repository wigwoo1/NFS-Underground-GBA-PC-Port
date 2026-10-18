from pathlib import Path
import ctypes as C,json,struct
p=Path('work/camera');events=json.loads((p/'stable-original-road-source.json').read_text())['roads'];geo=json.loads((p/'stable-road-geometric-inputs.json').read_text());joins=json.loads((p/'stable-road-source-transform-comparison.json').read_text())['checks'];maps=json.loads((p/'stable-road-emission-source-map.json').read_text())['checks'];rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=C.create_string_buffer(rom[0x627700:0x647700]);fn=C.CDLL(str((p/'road-source-ring.dll').resolve())).nf_road_source_ring;fn.argtypes=[C.c_void_p,C.c_uint]+[C.c_void_p]*5+[C.c_uint,C.c_void_p]
checks=[]
for e in events:
 j=next(j for j in joins if j['source']==e['source']);g=next(g for g in geo['roads'] if g['surface']==j['surface']);m=next(m for m in maps if m['source']==e['source']);world=(C.c_double*(len(g['vertices'])*3))(*(v for point in g['vertices'] for v in point));raw=struct.pack('<6I66i',*g['source_attributes_header'],*(v for pair in g['source_attributes'] for v in pair),*([0]*(64-len(g['source_attributes'])*2)))
 matrix=bytes.fromhex(e['blocks']['2']['hex']);out=(C.c_double*(64*5))();n=C.c_uint();assert fn(world,len(g['vertices']),raw,matrix,(C.c_int32*3)(120,87,128),table,out,64,C.byref(n));expected=[[r['six_words'][k] for k in (0,1,3,4,5)] for r in m['mapping']];actual=[list(out[i*5:i*5+5]) for i in range(n.value)];assert actual==expected,(actual,expected)
 checks.append(dict(source=e['source'],vertices=n.value,ring=actual))
report=dict(result='PASS',checks=checks,scope='Integrated world/raw camera/near/project source-order emission, exact17 original endpoints; affine sources, preview invocation and GPU remain pending.')
(p/'road-source-ring-tests.json').write_text(json.dumps(report,indent=2));print(report)

