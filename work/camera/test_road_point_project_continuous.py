from pathlib import Path
import ctypes as C,json,struct,math
p=Path('work/camera');maps=json.loads((p/'stable-road-emission-source-map.json').read_text());joins=json.loads((p/'stable-road-source-transform-comparison.json').read_text());geo=json.loads((p/'stable-road-geometric-inputs.json').read_text());projection=(C.c_int32*3)(120,87,128);rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=C.create_string_buffer(rom[0x627700:0x647700]);fn=C.CDLL(str((p/'road-point-project-continuous.dll').resolve())).nf_road_point_project_continuous;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];cases=continuity=0;maximum=0
for m,j,g in zip(maps['checks'],joins['checks'],geo['roads']):
 for row in m['mapping']:
  if row['near_generated']:continue
  index=row['source_vertex'];point=j['vertices'][index]['original_camera'];attrs=(C.c_int32*2)(*g['source_attributes'][index]);out=(C.c_double*5)();head=g['source_attributes_header'];assert fn((C.c_double*3)(*point),attrs,head[1],head[2],projection,table,out);expected=[row['six_words'][k] for k in (0,1,3,4,5)];assert list(out)==expected,(m['source'],index,list(out),expected);cases+=1
  for axis in range(3):
   for sign in (-1,1):
    moved=list(point);moved[axis]+=sign*1e-9;value=(C.c_double*5)();assert fn((C.c_double*3)(*moved),attrs,head[1],head[2],projection,table,value);delta=max(abs(value[k]-out[k]) for k in range(5));maximum=max(maximum,delta);assert delta<.01;continuity+=1
out=(C.c_double*5)(1,2,3,4,5);assert not fn((C.c_double*3)(0,0,0),(C.c_int32*2)(0,0),8,128,projection,table,out);assert list(out)==[1,2,3,4,5]
report=dict(result='PASS',original_source_identified_integer_vertices=cases,two_sided_projection_checks=continuity,epsilon=1e-9,max_attribute_delta=maximum,atomic_invalid_depth=True,scope='Retained source-corner projection/UV matches original stream by source identity, no screen matching. Near-generated positions/camera Q14 transform/native integration/GPU/fullmotion unverified.');(p/'road-point-project-continuous-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
