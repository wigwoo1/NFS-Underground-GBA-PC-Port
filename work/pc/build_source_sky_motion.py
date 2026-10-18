from pathlib import Path
import os,json,subprocess,hashlib
here=Path(__file__).resolve().parent;out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-source-sky-motion-tests');out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
args=['C:/msys64/mingw64/bin/gcc.exe','-O2','-shared','-Wall','-Wextra','-Werror','-ffp-contract=off',str(here/'source_sky_motion.c'),'-o',str(out/'source-sky-motion.dll'),'-lm'];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');subprocess.run(args,env=env,check=True)
r=dict(result='BUILT_SOURCE_SKY_MOTION_COMPONENT_TESTS_PENDING',dll_sha256=sha(out/'source-sky-motion.dll'),command=args,source_sha256={name:sha(here/name) for name in ['source_sky_motion.c','source_sky_motion.h','source_frame.h']},script_sha256=sha(Path(__file__)),live_integration=False,full_scene_60fps=False);(out/'sky-build-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['command','source_sha256']},indent=2))
