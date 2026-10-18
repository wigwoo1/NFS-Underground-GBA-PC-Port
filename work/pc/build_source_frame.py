from pathlib import Path
import hashlib,json,subprocess,sys,os
source=Path(__file__).parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-source-frame-tests';out.mkdir(exist_ok=True);gcc=Path('C:/msys64/mingw64/bin/gcc.exe');env=os.environ.copy();env['PATH']=str(gcc.parent)+';'+env['PATH']
command=[str(gcc),'-O2','-Wall','-Wextra','-Werror','-shared',str(source/'source_frame.c'),'-o',str(out/'source-frame.dll')]
with (out/'build.log').open('w') as log:subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report=dict(result='PASS_PC_SOURCE_FRAME_BUILD',command=command,compiler=subprocess.run([str(gcc),'--version'],env=env,capture_output=True,text=True,check=True).stdout.splitlines()[0],source_sha256={name:sha(source/name) for name in ('source_frame.c','source_frame.h')},adapter_sha256=sha(out/'source-frame.dll'))
(out/'build-report.json').write_text(json.dumps(report,indent=2))
for name in ('test_source_frame_component.py','test_source_frame_live.py'):subprocess.run([sys.executable,str(source/name)],env=env,check=True)
subprocess.run([sys.executable,str(source/'verify_source_frame.py')],env=env,check=True)
