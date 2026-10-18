from pathlib import Path
import ctypes as C,json
p=Path('work/camera');fn=C.CDLL(str((p/'road-near-continuous.dll').resolve())).nf_road_near_continuous;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_double,C.c_void_p,C.c_void_p]
endpoint_checks=0;movement=0;maximum=0
def verify_component(points,a,b,g,point,attrs):
 global endpoint_checks,movement,maximum
 aa=points[a]+g['source_attributes'][a];bb=points[b]+g['source_attributes'][b];out=(C.c_double*5)();assert fn((C.c_double*5)(*aa),(C.c_double*5)(*bb),64,buf,out);assert list(out)==point+attrs;endpoint_checks+=1
 for endpoint in range(2):
  for axis in range(5):
   pair=[aa.copy(),bb.copy()];pair[endpoint][axis]-=1e-8;l=(C.c_double*5)();assert fn((C.c_double*5)(*pair[0]),(C.c_double*5)(*pair[1]),64,buf,l)
   pair[endpoint][axis]+=2e-8;r=(C.c_double*5)();assert fn((C.c_double*5)(*pair[0]),(C.c_double*5)(*pair[1]),64,buf,r)
   delta=max(abs(x-y) for x,y in zip(l,r));maximum=max(maximum,delta);assert delta<.01;movement+=1
s=(p/'test_road_world_near_project.py').read_text();s=s.replace('  out=(C.c_double*5)();head=', '  verify_component(points,a,b,g,point,attrs)\n  out=(C.c_double*5)();head=')
# Keep the source oracle's existing report separate.
s=s.replace('road-world-near-project-tests.json','road-near-component-endpoint-tests.json');exec(compile(s,'near_component_endpoint','exec'),globals())
out=(C.c_double*5)(*range(5));assert not fn((C.c_double*5)(0,0,100,0,0),(C.c_double*5)(1,0,200,0,0),64,buf,out);assert list(out)==list(range(5))
report=dict(result='PASS',exact_near_endpoints=endpoint_checks,two_sided_edge_checks=movement,max_delta=maximum,atomic_non_crossing_rejection=True,scope='Bounded fixed near plane component only; topology boundary and live motion not verified.')
(p/'road-near-continuous-tests.json').write_text(json.dumps(report,indent=2));print(report)

