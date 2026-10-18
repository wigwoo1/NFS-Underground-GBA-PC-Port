from pathlib import Path
import hashlib,json,subprocess,os
here=Path(__file__).resolve().parent;root=here.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-recipe-mesh-tests';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
prior=base/'NFSUG-pc-recipe-geometry-tests/geometry-build-report.json';r=json.loads(prior.read_text())
for path,h in r['source_sha256'].items():assert sha(Path(path))==h
files=[here/n for n in ['recipe_mesh.c','recipe_material.c','recipe_geometry.c','source_road.c']]+[root/'work/camera/rigid_motion.c'];args=['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-ffp-contract=off','-shared']+[str(p) for p in files]+['-o',str(out/'recipe-mesh.dll'),'-lm'];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');subprocess.run(args,env=env,check=True)
files += [here/n for n in ['recipe_mesh.h','recipe_material.h','recipe_geometry.h','recipe_store.h','source_road.h','source_frame.h']]+[root/'work/camera/rigid_motion.h']
b=dict(result='BUILT_RECIPE_TRIANGLES_AND_INDEXED_MATERIALS_TESTS_PENDING',command=args,dll_sha256=sha(out/'recipe-mesh.dll'),source_sha256={str(p):sha(p) for p in files},geometry_receipt_sha256=sha(prior),script_sha256=sha(Path(__file__)),full_scene_60fps=False)
(out/'mesh-build-report.json').write_text(json.dumps(b,indent=2));print(b['result'],b['dll_sha256'])
