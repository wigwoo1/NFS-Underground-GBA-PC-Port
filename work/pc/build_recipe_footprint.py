from pathlib import Path
import json,hashlib,subprocess,os
here=Path(__file__).resolve().parent;root=here.parent.parent;out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-recipe-footprint-tests');out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
prior=json.loads((out.parent/'NFSUG-pc-recipe-mesh-tests/mesh-build-report.json').read_text())
for p,h in prior['source_sha256'].items():assert sha(p)==h,p
sources=[here/'recipe_footprint.c',here/'recipe_geometry.c',here/'source_road.c',root/'work/camera/rigid_motion.c'];args=['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-ffp-contract=off','-shared']+[str(p) for p in sources]+['-o',str(out/'recipe-footprint.dll'),'-lm'];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');subprocess.run(args,env=env,check=True)
sources += [here/'recipe_footprint.h',here/'recipe_geometry.h',here/'source_road.h',here/'recipe_store.h',root/'work/camera/rigid_motion.h'];r=dict(result='BUILT_SOURCE_PLANE_FOOTPRINT_TESTS_PENDING',dll_sha256=sha(out/'recipe-footprint.dll'),command=args,source_sha256={str(p):sha(p) for p in sources},script_sha256=sha(Path(__file__)),full_scene_60fps=False)
(out/'footprint-build-report.json').write_text(json.dumps(r,indent=2));print(r['result'],r['dll_sha256'])
