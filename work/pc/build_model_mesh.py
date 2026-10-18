from pathlib import Path
import hashlib,json,subprocess,os,sys,uuid
source=Path(__file__).parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-model-tests';out.mkdir(exist_ok=True);gcc=Path('C:/msys64/mingw64/bin/gcc.exe');jdk=base/'android-tools/jdk-21.0.12.1+1/bin';env=os.environ.copy();env['PATH']=str(gcc.parent)+';'+env['PATH']
command=[str(gcc),'-O2','-Wall','-Wextra','-Werror','-ffp-contract=off','-shared',str(source/'source_frame.c'),str(source/'model_mesh.c'),'-o',str(out/'source-model.dll'),'-lm']
with (out/'build.log').open('w') as log:subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
classes=out/('classes-'+uuid.uuid4().hex[:8]);java=root/'work/android/java/org/codex/nfsugpreview';subprocess.run([str(jdk/'javac.exe'),'--release','8','-sourcepath',str(java.parents[2]),'-d',str(classes),str(source/'PcModelReferenceExport.java')],env=env,check=True);subprocess.run([str(jdk/'java.exe'),'-Xmx256m','-cp',str(classes),'org.codex.nfsugpreview.PcModelReferenceExport',str(base/'NFSUG-background-owner-api-fixtures'),str(out/'references')],env=env,check=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
java_inputs={}
for path in classes.rglob('*.class'):
 name=path.name.split('$')[0].split('.')[0]+'.java';file=source/name if name=='PcModelReferenceExport.java' else java/name;java_inputs[str(file)]=sha(file)
report=dict(result='PASS_PC_MODEL_BUILD',command=command,source_sha256={name:sha(source/name) for name in ['source_frame.c','source_frame.h','model_mesh.c','model_mesh.h']},dll_sha256=sha(out/'source-model.dll'),java_oracle_sources=java_inputs,source_reference_inputs={str(p):sha(p) for p in (base/'NFSUG-background-owner-api-fixtures').glob('source-race-background-*.nrb')},reference_sha256={p.name:sha(p) for p in (out/'references').iterdir() if p.is_file()})
(out/'build-report.json').write_text(json.dumps(report,indent=2));subprocess.run([sys.executable,str(source/'test_model_mesh.py')],env=env,check=True);subprocess.run([sys.executable,str(source/'verify_model_mesh.py')],env=env,check=True)
