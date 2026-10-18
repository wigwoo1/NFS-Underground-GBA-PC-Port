from pathlib import Path
import ctypes as C,json
p=Path('work/camera');dll=C.CDLL(str((p/'road-point-project-continuous.dll').resolve()));fn=dll.nf_road_point_project_fractional;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p]
nearfn=C.CDLL(str((p/'road-near-continuous.dll').resolve())).nf_road_near_continuous;nearfn.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_void_p,C.c_void_p]
exec(compile((p/'test_road_world_near_project.py').read_text(),'source_setup','exec'),globals())
checks=0;maxgap=0
for e in events:
 j=next(j for j in joins if j['source']==e['source']);g=next(g for g in geo['roads'] if g['surface']==j['surface']);mapping=next(m for m in maps if m['source']==e['source']);matrix=(C.c_int32*12)(*struct.unpack('<12i',bytes.fromhex(e['blocks']['2']['hex'])))
 def pipeline(edge,dx):
  pair=[]
  for index in (edge,(edge+1)%len(g['vertices'])):
   v=g['vertices'][index].copy();v[0]+=dx;c=(C.c_double*3)();assert cam((C.c_double*3)(*v),matrix,c);pair.append(list(c)+g['source_attributes'][index])
  crossing=(C.c_double*5)();assert nearfn((C.c_double*5)(*pair[0]),(C.c_double*5)(*pair[1]),64,buf,crossing)
  out=(C.c_double*5)();head=g['source_attributes_header'];assert fn((C.c_double*3)(*crossing[:3]),(C.c_double*2)(*crossing[3:]),head[1],head[2],(C.c_int32*3)(120,87,128),buf,out);return list(out)
 for row in mapping['mapping']:
  if not row['near_generated']:continue
  base=pipeline(row['source_edge'],0);assert base==[row['six_words'][k] for k in (0,1,3,4,5)]
  for shift in (-.5,-.25,0,.25,.5):
   a=pipeline(row['source_edge'],shift-1e-9);b=pipeline(row['source_edge'],shift+1e-9);gap=max(abs(x-y) for x,y in zip(a,b));maxgap=max(maxgap,gap);assert gap<.01;checks+=1
out=(C.c_double*5)(1,2,3,4,5);assert not fn((C.c_double*3)(0,0,64),(C.c_double*2)(float('nan'),0),8,128,(C.c_int32*3)(120,87,128),buf,out);assert list(out)==[1,2,3,4,5]
report=dict(result='PASS',exact_near_projected_endpoints=4,composed_world_translation_checks=checks,max_projected_attribute_gap=maxgap,invalid_attribute_atomic=True,scope='Fixed raw camera matrix, fractional world X translation and UV propagation through near/project components; moving camera rotation and GPU/fullscene not verified.')
(p/'road-composed-fractional-tests.json').write_text(json.dumps(report,indent=2));print(report)
