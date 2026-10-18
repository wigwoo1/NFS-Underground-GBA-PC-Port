import random,time,json
from pathlib import Path
from owned_source_native_depth_rectangle_candidate import determinant
from owned_source_indexed_determinant_candidate import indexed_determinant
rng=random.Random(572);cases=[]
for n in range(3,33):
 for _ in range(100):
  points=tuple((rng.uniform(-32768,32767),rng.uniform(-32768,32767)) for i in range(40));ids=tuple(rng.sample(range(40),n));assert determinant([points[i] for i in ids])==indexed_determinant(points,ids);cases.append((points,ids))
bench={}
for name,fn in [('original',lambda p,i:determinant([p[x] for x in i])),('indexed',indexed_determinant)]:
 t=time.perf_counter_ns()
 for _ in range(40):
  for p,i in cases:fn(p,i)
 bench[name]=(time.perf_counter_ns()-t)/1e6
out=dict(result='PASS',exact_cases=len(cases),face_sizes=[3,32],benchmark_120000_calls_ms=bench,scope='Synthetic finite-coordinate exact arithmetic and captured complete4K pixel parity are component evidence, not sustained live cadence')
Path('work/camera/indexed-determinant-tests.json').write_text(json.dumps(out,indent=2));print(out)
Path('work/camera/run_indexed_determinant_candidate.py').write_text("import owned_source_native_depth_rectangle_candidate as original\nfrom owned_source_indexed_determinant_candidate import SourceFaceDeterminants\noriginal.SourceFaceDeterminants=SourceFaceDeterminants\nimport runpy\nrunpy.run_path('work/camera/run_segmented_wait_profile_candidate.py',run_name='__main__')\n")
