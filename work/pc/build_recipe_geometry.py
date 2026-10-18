from pathlib import Path
import hashlib,json,subprocess,os
here=Path(__file__).resolve().parent;root=here.parent.parent;out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-recipe-geometry-tests');out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=[here/'recipe_geometry.c',here/'source_road.c',root/'work/camera/rigid_motion.c'];args=['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-ffp-contract=off','-shared']+[str(p) for p in files]+['-o',str(out/'recipe-geometry.dll'),'-lm'];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');subprocess.run(args,env=env,check=True)
files += [here/'recipe_geometry.h',here/'recipe_store.h',here/'source_road.h',here/'source_frame.h',root/'work/camera/rigid_motion.h']
r=dict(result='BUILT_OWNED_RECIPE_WORLD_GEOMETRY_TESTS_PENDING',command=args,dll_sha256=sha(out/'recipe-geometry.dll'),source_sha256={str(p):sha(p) for p in files},script_sha256=sha(Path(__file__)),live_host_changed=False,full_scene_60fps=False)
(out/'geometry-build-report.json').write_text(json.dumps(r,indent=2));print(r['result'],r['dll_sha256'])
