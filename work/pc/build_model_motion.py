from pathlib import Path
import os,subprocess,json,hashlib
here=Path(__file__).resolve().parent;root=here.parent.parent;out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-model-motion-tests');out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=[here/'model_motion.c',here/'model_mesh.c',here/'source_frame.c',root/'work/camera/rigid_motion.c'];args=['C:/msys64/mingw64/bin/gcc.exe','-O2','-shared','-Wall','-Wextra','-Werror','-ffp-contract=off']+[str(p) for p in files]+['-o',str(out/'model-motion.dll'),'-lm'];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');subprocess.run(args,env=env,check=True)
r=dict(result='BUILT_MODEL_MOTION_COMPONENT_TESTS_PENDING',command=args,dll_sha256=sha(out/'model-motion.dll'),source_sha256={str(p):sha(p) for p in files+[here/'model_motion.h',here/'model_mesh.h',here/'source_frame.h',root/'work/camera/rigid_motion.h']},script_sha256=sha(Path(__file__)),live_host_changed=False,full_scene_60fps=False)
(out/'motion-build-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['command','source_sha256']},indent=2))
