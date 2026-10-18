from pathlib import Path
import subprocess,sys,os,json,hashlib,uuid,ctypes as C
source=Path(__file__).resolve().parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-world-mesh-tests';out.mkdir(exist_ok=True);jdk=base/'android-tools/jdk-21.0.12.1+1/bin';env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Revalidate extended world reader, including existing live-source behavior.
subprocess.run([sys.executable,str(source/'build_source_world.py')],check=True,env=env)
road=json.loads((base/'NFSUG-pc-road-math-tests/road-math-build-report.json').read_text())
for name in ['source_road.c','source_road.h']:assert sha(source/name)==road['source_sha256'][name]
road_ref=base/'NFSUG-pc-road-math-tests/references/reciprocal.bin';assert sha(road_ref)==road['reference_sha256']['reciprocal.bin']
native=['source_frame.c','source_frame.h','source_world.c','source_world.h','source_road.c','source_road.h','world_mesh.c','world_mesh.h']
cmd=['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-ffp-contract=off','-shared']+[str(source/n) for n in native if n.endswith('.c')]+['-o',str(out/'world-mesh.dll'),'-lm'];subprocess.run(cmd,check=True,env=env)
subprocess.run([sys.executable,str(source/'make_world_mesh_inputs.py')],check=True,env=env)
java=root/'work/android/java/org/codex/nfsugpreview';classes=out/('classes-'+uuid.uuid4().hex[:8]);subprocess.run([str(jdk/'javac.exe'),'--release','8','-sourcepath',str(java.parents[2]),'-d',str(classes),str(source/'PcWorldMeshReferenceExport.java')],check=True,env=env)
subprocess.run([str(jdk/'java.exe'),'-Xmx512m','-cp',str(classes),'org.codex.nfsugpreview.PcWorldMeshReferenceExport',str(out/'inputs'),str(out/'references')],check=True,env=env)
subprocess.run([sys.executable,str(source/'test_world_mesh_live.py')],check=True,env=env)
a=json.loads((out/'world-mesh-report.json').read_text());b=json.loads((out/'world-mesh-live-report.json').read_text())
assert a['worlds']==34 and a['surfaces']==405 and a['triangle_vertices']==3006 and a['texture_planes']==1002 and a['inconsistent_camera_cases_rejected']==9 and len(a['modes'])==11
assert b['surfaces']==388 and b['triangle_vertices']==2943 and b['original_prefix_frames']==296 and b['mesh_survives_world_frame_and_core_free'] and b['projection_never_steps_logic']
for name,digest in a['source_sha256'].items():assert sha(source/name)==digest
assert a['test_sha256']==sha(source/'test_world_mesh.py') and b['test_sha256']==sha(source/'test_world_mesh_live.py') and a['dll_sha256']==b['dll_sha256']==sha(out/'world-mesh.dll')
java_sources={}
for file in classes.rglob('*.class'):
 name=file.name.split('$')[0].split('.')[0]+'.java';path=source/name if name=='PcWorldMeshReferenceExport.java' else java/name;java_sources[str(path)]=sha(path)
exports=['nf_pc_world_model','nf_pc_world_mesh','nf_pc_world_mesh_free','nf_pc_world_mesh_info','nf_pc_world_mesh_buffer','nf_pc_world_mesh_plane']
with os.add_dll_directory('C:/msys64/mingw64/bin'):dll=C.CDLL(str(out/'world-mesh.dll'))
for name in exports:assert getattr(dll,name)
names=native+['PcWorldMeshReferenceExport.java','make_world_mesh_inputs.py','test_world_mesh.py','test_world_mesh_live.py','build_world_mesh.py']
r=dict(result='PASS_PC_WORLD_MESH_INTEGRATION',command=cmd,source_sha256={n:sha(source/n) for n in names},java_oracle_sources=java_sources,input_sha256={p.name:sha(p) for p in (out/'inputs').glob('*.nsp')},reference_sha256={p.name:sha(p) for p in (out/'references').glob('*.mesh')},prerequisite_receipts_sha256={str(p):sha(p) for p in [base/'NFSUG-pc-world-tests/world-build-report.json',base/'NFSUG-pc-road-math-tests/road-math-build-report.json']},dll_sha256=sha(out/'world-mesh.dll'),core_sha256=b['core_sha256'],exports=exports,actual_surfaces=388,synthetic_surfaces=17,all_material_modes=11,triangle_vertices=3006,texture_planes=1002,camera_double_values=5598,invalid_camera_cases=9,original_prefix_frames=296,world_mesh_projection_verified=True,gpu_world_drawing=False,full_scene=False,playable_native_release=False,full_scene_60fps=False,reports_sha256={n:sha(out/n) for n in ['world-mesh-report.json','world-mesh-live-report.json']})
(out/'world-mesh-build-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['command','source_sha256','java_oracle_sources','input_sha256','reference_sha256','prerequisite_receipts_sha256']},indent=2))
