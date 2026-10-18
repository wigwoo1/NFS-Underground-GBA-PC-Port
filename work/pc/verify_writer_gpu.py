from pathlib import Path
import json,hashlib,subprocess,sys
here=Path(__file__).resolve().parent;out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-writer-gpu-tests')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
rows=[]
for name in ['test_writer_gpu.py','test_writer_gpu_synthetic.py','test_writer_gpu_guards.py','test_writer_gpu_regression.py']:
 print('RUN',name,flush=True);subprocess.run([sys.executable,str(here/name)],check=True);rows.append(dict(test=name,sha256=sha(here/name)));(out/'writer-verification-report.json').write_text(json.dumps(dict(result='RUNNING_WRITER_GPU_REGRESSIONS',tests=rows),indent=2))
r=dict(result='PASS_WRITER_GPU_ACTUAL_SYNTHETIC_OWNERSHIP_AND_EXISTING_SCENE',tests=rows,script_sha256=sha(Path(__file__)),gpu_dll_sha256=sha(out/'recipe-gpu.dll'),full_scene_60fps=False);(out/'writer-verification-report.json').write_text(json.dumps(r,indent=2));print(r['result'])
