from pathlib import Path
import json,hashlib,subprocess,os
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-recipe-region-tests';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
for name in ['NFSUG-pc-recipe-footprint-tests/footprint-build-report.json','NFSUG-pc-recipe-coverage-tests/coverage-build-report.json']:
 b=json.loads((base/name).read_text())
 for p,h in b['source_sha256'].items():assert sha(p)==h,p
sources=[here/n for n in ['recipe_regions.c','recipe_coverage.c','source_frame.c','recipe_footprint.c','recipe_geometry.c','source_road.c','recipe_mesh.c']]+[root/'work/camera/rigid_motion.c'];args=['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-ffp-contract=off','-shared']+[str(p) for p in sources]+['-o',str(out/'recipe-regions.dll'),'-lm'];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');subprocess.run(args,env=env,check=True)
sources += [here/n for n in ['recipe_regions.h','recipe_coverage.h','source_frame.h','recipe_footprint.h','recipe_geometry.h','source_road.h','recipe_mesh.h','recipe_store.h']]+[root/'work/camera/rigid_motion.h'];r=dict(result='BUILT_EXACT_COVERAGE_REGIONS_AND_TRANSPORT_TESTS_PENDING',dll_sha256=sha(out/'recipe-regions.dll'),command=args,source_sha256={str(p):sha(p) for p in sources},script_sha256=sha(Path(__file__)),full_scene_60fps=False)
(out/'region-build-report.json').write_text(json.dumps(r,indent=2));print(r['result'],r['dll_sha256'])
