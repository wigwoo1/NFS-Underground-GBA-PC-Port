from pathlib import Path
import ctypes as C,json
p=Path('work/camera');f=C.CDLL(str((p/'road-row-lattice-coverage.dll').resolve())).nf_road_row_lattice_coverage;f.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p];table=C.create_string_buffer((p/'road-correction-reciprocal.bin').read_bytes());checks=[]
for road in json.loads((p/'world-source-clipped-rings.json').read_text())['checks']:
 for shift in (-2,-1,0,1,2):
  results=[]
  for side in (-1,1):
   ring=[[v+(shift+side*1e-8 if k==0 else 0) for k,v in enumerate(r)] for r in road['clipped_ring']];data=(C.c_double*(len(ring)*6))(*(v for r in ring for v in r));out=(C.c_double*(38400*3))();assert f(data,len(ring),(C.c_uint16*4)(*road['bounds']),table,out);results.append(out)
  coveragegap=max(abs(results[0][i*3+2]-results[1][i*3+2]) for i in range(38400));changed=sum(abs(results[0][i*3+2]-results[1][i*3+2])>.1 for i in range(38400));checks.append(dict(command=road['command'],source_geometry_x_shift=shift,maximum_coverage_jump=coveragegap,jumping_destinations=changed))
report=dict(result='REJECTED_FOR_FULL_MOTION_ADOPTION',checks=checks,scope='Small X perturbations of world-derived source geometry expose paired-floor coverage jumps retained by row-only interpolation. Diagnostic geometry perturbation, not actual new camera pose or screen polygon matching.');(p/'road-row-lattice-x-continuity-audit.json').write_text(json.dumps(report,indent=2));print(report)
