from pathlib import Path
import subprocess,sys,os,json,hashlib,uuid,ctypes as C
source=Path(__file__).resolve().parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-world-gpu-tests';out.mkdir(exist_ok=True);jdk=base/'android-tools/jdk-21.0.12.1+1/bin';env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
prerequisite=base/'NFSUG-pc-world-material-tests/world-material-build-report.json';prior=json.loads(prerequisite.read_text());native=['source_frame.c','source_frame.h','source_world.c','source_world.h','source_road.c','source_road.h','world_mesh.c','world_mesh.h','world_material.c','world_material.h']
for n in native:assert sha(source/n)==prior['source_sha256'][n]
inputs=base/'NFSUG-pc-world-material-tests/inputs';material_refs=base/'NFSUG-pc-world-material-tests/references'
for n,digest in prior['input_sha256'].items():assert sha(inputs/n)==digest
for n,digest in prior['reference_sha256'].items():assert sha(material_refs/n)==digest
for p,digest in prior['java_oracle_sources'].items():assert sha(Path(p))==digest
# Keep established model/background consumer implementations unchanged.
protected={}
for receipt in [base/'NFSUG-pc-model-tests/model-gpu-build-report.json',base/'NFSUG-pc-background-tests/build-report.json']:
 r=json.loads(receipt.read_text())
 for n in ['model_gpu.c','model_gpu.h','background_gpu.c','background_gpu.h']:
  if n in r.get('source_sha256',{}):assert sha(source/n)==r['source_sha256'][n];protected[n]=sha(source/n)
# Palette buffers used for captured surfaces are independently Java-exported.
palette_build=json.loads((base/'NFSUG-pc-background-tests/build-report.json').read_text());palette_refs=base/'NFSUG-pc-background-tests/references'
for p in palette_refs.glob('*.palette.rgba'):assert sha(p)==palette_build['reference_sha256'][p.name]
native+=['world_gpu.c','world_gpu.h'];cmd=['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-ffp-contract=off','-shared']+[str(source/n) for n in native if n.endswith('.c')]+['-o',str(out/'world-gpu.dll'),'-lopengl32','-lgdi32','-luser32','-lm'];subprocess.run(cmd,check=True,env=env)
java=root/'work/android/java/org/codex/nfsugpreview';classes=out/('classes-'+uuid.uuid4().hex[:8]);subprocess.run([str(jdk/'javac.exe'),'--release','8','-sourcepath',str(java.parents[2]),'-d',str(classes),str(source/'PcWorldMeshReferenceExport.java')],check=True,env=env);subprocess.run([str(jdk/'java.exe'),'-Xmx512m','-cp',str(classes),'org.codex.nfsugpreview.PcWorldMeshReferenceExport',str(inputs),str(out/'references')],check=True,env=env)
for test in ['test_world_gpu.py','test_world_gpu_contract.py']:subprocess.run([sys.executable,str(source/test)],check=True,env=env)
r=json.loads((out/'world-gpu-report.json').read_text());c=json.loads((out/'world-gpu-contract-report.json').read_text());assert r['actual_surfaces']==388 and r['accepted_surfaces']==406 and r['targets']==413 and r['four_k_targets']==5 and r['world_free_render_thread_recreation_verified'];assert c['cases']==16 and c['pixel_comparisons']==66662400 and c['all_pixels_exact'];assert r['dll_sha256']==c['dll_sha256']==sha(out/'world-gpu.dll')
java_sources={str(java/'NativeSceneGpu.java'):sha(java/'NativeSceneGpu.java')}
for file in classes.rglob('*.class'):
 name=file.name.split('$')[0].split('.')[0]+'.java';path=source/name if name=='PcWorldMeshReferenceExport.java' else java/name;java_sources[str(path)]=sha(path)
exports=['nf_pc_world_gpu_open','nf_pc_world_gpu_close','nf_pc_world_gpu_error','nf_pc_world_gpu_renderer','nf_pc_world_gpu_draw']
with os.add_dll_directory('C:/msys64/mingw64/bin'):dll=C.CDLL(str(out/'world-gpu.dll'))
for n in exports:assert getattr(dll,n)
reference_runtime=base/'android-tools/sdk/emulator/lib64/gles_swiftshader';names=native+['gles_world_reference.py','gles_model_reference.py','PcWorldMeshReferenceExport.java','test_world_gpu.py','test_world_gpu_contract.py','build_world_gpu.py']
b=dict(result='PASS_PC_WORLD_GPU_EXECUTION_AND_EXACT_CONTRACTS_FIDELITY_OPEN',command=cmd,source_sha256={n:sha(source/n) for n in names},protected_gpu_sources=protected,java_oracle_sources=java_sources,input_sha256=prior['input_sha256'],material_reference_sha256=prior['reference_sha256'],mesh_reference_sha256={p.name:sha(p) for p in (out/'references').glob('*.mesh')},palette_reference_sha256={p.name:sha(p) for p in palette_refs.glob('*.palette.rgba')},reference_runtime_sha256={n:sha(reference_runtime/n) for n in ['libEGL.dll','libGLESv2.dll']},prerequisite_receipt_sha256=sha(prerequisite),dll_sha256=sha(out/'world-gpu.dll'),exports=exports,actual_surfaces=388,cross_gpu_targets=413,cross_gpu_pixels=r['pixel_comparisons'],cross_gpu_differences=r['mismatched_pixels'],exact_contract_cases=16,exact_contract_pixels=66662400,world_free_render_thread_recreation_verified=True,full_world_pixel_fidelity_verified=False,full_scene=False,playable_native_release=False,full_scene_60fps=False,reports_sha256={n:sha(out/n) for n in ['world-gpu-report.json','world-gpu-contract-report.json']},screenshots_sha256={n:sha(out/n) for n in ['source-lit-wall-4k.png','source-road-4k.png']})
(out/'world-gpu-build-report.json').write_text(json.dumps(b,indent=2));print(json.dumps({k:v for k,v in b.items() if k not in ['command','source_sha256','protected_gpu_sources','java_oracle_sources','input_sha256','material_reference_sha256','mesh_reference_sha256','palette_reference_sha256','reference_runtime_sha256']},indent=2))
