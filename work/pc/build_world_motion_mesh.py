from pathlib import Path
import os,subprocess,json,hashlib,re,argparse
here=Path(__file__).resolve().parent;root=here.parent.parent;out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-world-mesh-motion-tests');out.mkdir(exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--owner',action='store_true');options=parser.parse_args();library='world-mesh-motion.dll'
if options.owner:out=out.parent/'NFSUG-pc-world-owner-motion-tests';out.mkdir(exist_ok=True);library='world-owner-motion.dll'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=[here/n for n in ['world_motion_mesh.c','world_camera_motion.c','source_road.c','source_frame.c','source_world.c','world_mesh.c']]+[root/'work/camera'/n for n in ['rigid_motion.c','visibility_pose.c']]
if options.owner:files.append(here/'world_motion_owner.c')
args=['C:/msys64/mingw64/bin/gcc.exe','-O2','-shared','-Wall','-Wextra','-Werror','-ffp-contract=off']+[str(p) for p in files]+['-o',str(out/library),'-lm'];env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');subprocess.run(args,env=env,check=True)
inputs=set(files);pending=list(inputs)
while pending:
 p=pending.pop()
 for name in re.findall(r'#include\s+"([^"]+)"',p.read_text(encoding='utf-8')):
  dependency=(p.parent/name).resolve();assert dependency.is_file(),dependency
  if dependency not in inputs:inputs.add(dependency);pending.append(dependency)
r=dict(result='BUILT_WORLD_OWNER_MOTION_TESTS_PENDING' if options.owner else 'BUILT_WORLD_MESH_MOTION_COMPONENT_TESTS_PENDING',command=args,dll_sha256=sha(out/library),source_sha256={str(p):sha(p) for p in sorted(inputs)},script_sha256=sha(Path(__file__)),live_host_changed=False,full_scene_60fps=False)
(out/'motion-build-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['command','source_sha256']},indent=2))
