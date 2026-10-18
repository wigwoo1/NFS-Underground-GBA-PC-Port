from pathlib import Path
import subprocess,os,sys,json,hashlib
source=Path(__file__).resolve().parent
out=Path(r"C:\NFSUG-Workspace\NFSUG-pc-model-tests")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','')
# Existing independently exported model and palette references must still match their receipts.
subprocess.run([sys.executable,str(source/'verify_model_mesh.py')],check=True,env=env)
background=out.parent/'NFSUG-pc-background-tests'
build=json.loads((background/'build-report.json').read_text())
# Record every reference used below, including original Java exports.
references=list((out/'references').iterdir())+list((background/'references').glob('*.palette.rgba'))
names=['source_frame.c','source_frame.h','model_mesh.c','model_mesh.h','model_gpu.c','model_gpu.h','test_model_gpu.py']
cmd=['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-ffp-contract=off','-shared']+[str(source/n) for n in ['source_frame.c','model_mesh.c','model_gpu.c']]+['-o',str(out/'model-gpu.dll'),'-lopengl32','-lgdi32','-luser32','-lm']
subprocess.run(cmd,check=True,env=env)
subprocess.run([sys.executable,str(source/'test_model_gpu.py')],check=True,env=env)
r=json.loads((out/'model-gpu-report.json').read_text());assert len(r['exact_material_cases'])==8 and r['exact_material_pixels']==33331200 and r['models']==32 and r['targets']==37
assert all(c['exact'] for c in r['exact_material_cases']) and r['short_output_wrong_thread_empty_clip_guards'] and r['context_recreated_on_different_thread']
assert r['dll_sha256']==sha(out/'model-gpu.dll') and r['test_sha256']==sha(source/'test_model_gpu.py')
report=dict(result='PASS_PC_MODEL_GPU_COMPONENT_EXECUTION_FIDELITY_OPEN',command=cmd,source_sha256={n:sha(source/n) for n in names},reference_sha256={str(f):sha(f) for f in references},dll_sha256=sha(out/'model-gpu.dll'),screenshot_sha256=sha(out/'source-model-4k.png'),model_gpu_report_sha256=sha(out/'model-gpu-report.json'),exact_material_pixels=r['exact_material_pixels'],model_pixel_comparisons=r['pixel_comparisons'],model_pixel_differences=r['mismatched_pixels'],exact_model_fidelity_verified=False,full_scene=False,playable_native_release=False,full_scene_60fps=False)
(out/'model-gpu-build-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['command','source_sha256','reference_sha256']},indent=2))
