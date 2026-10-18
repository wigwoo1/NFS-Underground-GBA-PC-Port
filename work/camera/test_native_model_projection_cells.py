import ctypes as C,json,struct,time
from pathlib import Path
from owned_motion_pairs import records
from owned_source_depth_rectangle_candidate import SourceFaceDeterminants as Reference
from owned_source_native_depth_rectangle_candidate import SourceFaceDeterminants as Native
p=Path('work/camera');r=json.loads((p/'prototype-runs/owned-native-1791267744113946700.json').read_text());d=C.CDLL(str((p/'owned-sky-source-face-candidate.dll').resolve()));table=(C.c_uint32*32768)(*struct.unpack('<32768I',(p/'road-correction-reciprocal.bin').read_bytes()[:131072]));checks=0;maximum=0
for capture in r['wall_diagnostic_frames']:
 for row in records(Path(capture['regenerated']).read_bytes())['records']:
  if row['kind']!=3:continue
  ref=Reference(row,row,d,table);native=Native(row,row,d,table)
  for shift in (0,.125,.25,.5,.75):
   m=list(ref.matrices[0]);m[9]+=shift;m[10]-=shift;m[11]+=shift
   a=ref.projected(m,ref.scales[0],ref.centers[0]);b=native.projected(m,native.scales[0],native.centers[0])
   for pa,pb in zip(a,b):
    error=max(abs(x-y) for x,y in zip(pa,pb));maximum=max(maximum,error);assert error<1e-8;checks+=2
m=ref.matrices[0];timings={}
for name,obj in (('python',ref),('native',native)):
 start=time.perf_counter_ns()
 for _ in range(100):obj.projected(m,obj.scales[0],obj.centers[0])
 timings[name]=(time.perf_counter_ns()-start)/1e6
lib=C.CDLL(str((p/'source-model-project-cells-candidate.dll').resolve()));fn=lib.nf_source_model_project_cells;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint32,C.c_void_p,C.c_void_p,C.c_void_p];matrix=(C.c_double*12)(*m);center=(C.c_int32*2)(*ref.centers[0]);out=(C.c_double*(2*len(ref.vertices)))(*([123.]*(2*len(ref.vertices))));matrix[11]=-100000;assert fn(matrix,native.native_vertices,len(ref.vertices),ref.scales[0],center,table,out)==37 and all(x==123 for x in out)
root=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/native-model-projection-cells-20261007');root.mkdir(exist_ok=True);result=dict(result='PASS_NATIVE_PROJECTION_EQUIVALENCE',coordinate_checks=checks,max_error=maximum,benchmark_100_calls_ms=timings,component_speedup=timings['python']/timings['native'],invalid_domain_preserves_output=True,scope='Captured models and fractional translations, native bulk classification projection matches Python reference; isolated component speed, not live cadence proof.');(root/'tests.json').write_text(json.dumps(result,indent=2));(root/Path(__file__).name).write_text(Path(__file__).read_text());print(json.dumps(result,indent=2))
