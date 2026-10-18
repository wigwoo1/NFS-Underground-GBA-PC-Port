from pathlib import Path
import os,subprocess,json,hashlib,re
here=Path(__file__).resolve().parent;root=here.parent.parent;out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-world-camera-motion-tests');out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=[here/'world_camera_motion.c',here/'source_road.c',here/'source_frame.c',here/'source_world.c',here/'world_mesh.c',root/'work/camera/rigid_motion.c',root/'work/camera/visibility_pose.c'];args=['C:/msys64/mingw64/bin/gcc.exe','-O2','-shared','-Wall','-Wextra','-Werror','-ffp-contract=off']+[str(p) for p in files]+['-o',str(out/'world-camera-motion.dll'),'-lm'];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');subprocess.run(args,env=env,check=True)
headers=[here/'world_camera_motion.h',here/'source_road.h',here/'source_frame.h',here/'source_world.h',root/'work/camera/rigid_motion.h',root/'work/camera/visibility_snapshot.h']
inputs=set(files+headers);pending=list(inputs)
while pending:
 p=pending.pop()
 for name in re.findall(r'#include\s+"([^"]+)"',p.read_text(encoding='utf-8')):
  dependency=(p.parent/name).resolve();assert dependency.is_file(),dependency
  if dependency not in inputs:inputs.add(dependency);pending.append(dependency)
r=dict(result='BUILT_WORLD_CAMERA_MOTION_COMPONENT_TESTS_PENDING',command=args,dll_sha256=sha(out/'world-camera-motion.dll'),source_sha256={str(p):sha(p) for p in sorted(inputs)},script_sha256=sha(Path(__file__)),live_host_changed=False,full_scene_60fps=False)
(out/'motion-build-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['command','source_sha256']},indent=2))
