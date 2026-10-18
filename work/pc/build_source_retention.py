from pathlib import Path
import os,sys,subprocess,json,hashlib,uuid
source=Path(__file__).resolve().parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-retention-tests';out.mkdir(exist_ok=True);env=dict(os.environ);env['PATH']='C:/msys64/mingw64/bin;'+env.get('PATH','');jdk=base/'android-tools/jdk-21.0.12.1+1/bin'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
subprocess.run([sys.executable,str(source/'verify_source_frame.py')],check=True,env=env)
cmd=['C:/msys64/mingw64/bin/gcc.exe','-O2','-Wall','-Wextra','-Werror','-ffp-contract=off','-shared',str(source/'source_frame.c'),str(source/'source_retention.c'),'-o',str(out/'source-retention.dll')]
subprocess.run(cmd,check=True,env=env)
java=root/'work/android/java/org/codex/nfsugpreview';classes=out/('classes-'+uuid.uuid4().hex[:8]);subprocess.run([str(jdk/'javac.exe'),'--release','8','-sourcepath',str(java.parents[2]),'-d',str(classes),str(source/'PcRetentionReferenceExport.java')],check=True,env=env)
subprocess.run([str(jdk/'java.exe'),'-Xmx512m','-cp',str(classes),'org.codex.nfsugpreview.PcRetentionReferenceExport',str(base/'NFSUG-background-owner-api-fixtures'),str(out/'references')],check=True,env=env)
subprocess.run([sys.executable,str(source/'test_source_retention.py')],check=True,env=env)
r=json.loads((out/'retention-report.json').read_text());assert r['cases']==34 and r['cells']==307441 and r['original_prefix_frames']==296 and r['all_indices_and_source_records_exact'] and r['owned_after_core_close'];assert r['dll_sha256']==sha(out/'source-retention.dll') and r['core_sha256']==sha(base/'NFSUG-android-background-jni-native-local/capture-host.dll')
java_sources={}
for file in classes.rglob('*.class'):
 name=file.name.split('$')[0].split('.')[0]+'.java';p=source/name if name=='PcRetentionReferenceExport.java' else java/name;java_sources[str(p)]=sha(p)
b=dict(result='PASS_PC_SOURCE_RETENTION',source_sha256={n:sha(source/n) for n in ['source_frame.c','source_frame.h','source_retention.c','source_retention.h','PcRetentionReferenceExport.java','test_source_retention.py','build_source_retention.py']},java_oracle_sources=java_sources,fixture_sha256={str(p):sha(p) for pattern in ['source-race-background-*.nrb','owner-*.nrh','owner-*.nwh','owner-*.nrp'] for p in (base/'NFSUG-background-owner-api-fixtures').glob(pattern)},references_sha256={p.name:sha(p) for p in (out/'references').glob('*.ret')},dll_sha256=sha(out/'source-retention.dll'),report_sha256=sha(out/'retention-report.json'),cases=r['cases'],cells=r['cells'],original_prefix_frames=r['original_prefix_frames'],gpu_submitted=False,playable_native_release=False,full_scene_60fps=False)
(out/'retention-build-report.json').write_text(json.dumps(b,indent=2));print(json.dumps({k:v for k,v in b.items() if not isinstance(v,dict)},indent=2))
