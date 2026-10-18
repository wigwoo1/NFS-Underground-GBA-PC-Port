from pathlib import Path
import subprocess,sys,json,hashlib
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-writer-native-scene-tests'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
rows=[]
for name in ['test_writer_gpu.py','test_writer_gpu_synthetic.py','test_writer_gpu_guards.py','test_writer_gpu_clipping.py','test_writer_gpu_regression.py']:
 original=here/name;source=original.read_text().replace('NFSUG-pc-writer-gpu-tests','NFSUG-pc-writer-native-scene-tests')
 if name=='test_writer_gpu_guards.py':source=source.replace('boot=original.read_text().split',"boot=original.read_text().replace('NFSUG-pc-writer-gpu-tests','NFSUG-pc-writer-native-scene-tests').split")
 staged=out/('executed-'+name)
 staged.write_text('exec(compile('+repr(source)+','+repr(str(original))+',"exec"),{"__file__":'+repr(str(original))+',"__name__":"__main__"})\n')
 subprocess.run([sys.executable,str(staged)],check=True);rows.append(dict(test=name,source_sha256=sha(original),executed_source_sha256=hashlib.sha256(source.encode()).hexdigest(),launcher_sha256=sha(staged)))
 (out/'writer-scene-regression-dispatch.json').write_text(json.dumps(dict(result='RUNNING_SCENE_WRITER_REGRESSIONS',tests=rows),indent=2))
r=dict(result='PASS_SCENE_WRITER_ALL_FROZEN_TEXTURE_AND_SCENE_REGRESSIONS',tests=rows,script_sha256=sha(Path(__file__)),gpu_dll_sha256=sha(out/'recipe-gpu.dll'),full_scene_60fps=False)
(out/'writer-scene-regression-dispatch.json').write_text(json.dumps(r,indent=2));print(r['result'])
