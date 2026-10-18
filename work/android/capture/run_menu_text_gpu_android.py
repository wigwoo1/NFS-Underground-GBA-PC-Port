from pathlib import Path
import subprocess,json,hashlib,time
base=Path(r'C:\NFSUG-Workspace');adb=base/'android-tools/sdk/platform-tools/adb.exe';build=base/'NFSUG-android-local/app-menu-text-gpu-tests';fixtures=base/'NFSUG-android-owned-text-local'
def run(args,timeout=45):return subprocess.run([str(adb),'-s','emulator-5556',*map(str,args)],check=True,capture_output=True,timeout=timeout).stdout
for attempt in range(60):
 try:
  if run(['shell','getprop','sys.boot_completed'],5).strip()==b'1':break
 except (subprocess.CalledProcessError,subprocess.TimeoutExpired):pass
 time.sleep(1)
else:raise RuntimeError('Owned emulator not ready')
assert run(['emu','avd','name']).decode().splitlines()[0].strip()=='NFSUG_API30'
host=json.loads((fixtures/'menu-text-decode-report.json').read_text());manifest=json.loads((build/'apk-build-report.json').read_text())
for name,digest in host['source_sha256'].items():
 key=('tests' if name=='MenuTextTest.java' else 'java')+'/org/codex/nfsugpreview/'+name
 assert manifest['source_sha256'][key]==digest
print(run(['install','-r',build/'NFSUG-Android-Core-Preview.apk']).decode(),flush=True)
run(['shell','run-as','org.codex.nfsugpreview','mkdir','-p','files/menu-text-fixtures'])
for name,digest in host['fixture_sha256'].items():
 assert hashlib.sha256((fixtures/name).read_bytes()).hexdigest()==digest
 temp='/data/local/tmp/nfsug-'+name;private='files/menu-text-fixtures/'+name
 try:run(['push',fixtures/name,temp]);run(['shell','run-as','org.codex.nfsugpreview','cp',temp,private])
 finally:run(['shell','rm','-f',temp])
 assert run(['exec-out','run-as','org.codex.nfsugpreview','sha256sum',private]).decode().split()[0]==digest
result=run(['shell','am','instrument','-w','-r','org.codex.nfsugpreview/.MenuTextGpuInstrumentation'],120).decode();(build/'menu-text-gpu-run.log').write_text(result);print(result,flush=True)
assert 'PASS_ANDROID_MENU_TEXT_GPU' in result and 'INSTRUMENTATION_CODE: -1' in result
report=json.loads(run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/menu-text-gpu-report.json']))
assert report['pixel_checks']==8371200 and report['covered_samples']>0 and report['transparent_samples']>0;report['apk_sha256']=manifest['sha256'];report['fixtures']=host['fixture_sha256'];(build/'menu-text-gpu-android-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
