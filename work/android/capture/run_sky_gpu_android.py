from pathlib import Path
import subprocess,json,hashlib,time
base=Path(r'C:\NFSUG-Workspace');root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');build=base/'NFSUG-android-local/app-sky-gpu-tests';fixtures=base/'NFSUG-android-sky-local';adb=base/'android-tools/sdk/platform-tools/adb.exe'
def run(args,timeout=45):return subprocess.run([str(adb),'-s','emulator-5556',*map(str,args)],check=True,capture_output=True,timeout=timeout).stdout
for i in range(60):
 try:
  if run(['shell','getprop','sys.boot_completed'],5).strip()==b'1':break
 except (subprocess.CalledProcessError,subprocess.TimeoutExpired):pass
 time.sleep(1)
else:raise RuntimeError('Owned emulator not booted')
assert run(['emu','avd','name']).decode().splitlines()[0].strip()=='NFSUG_API30'
host=json.loads((fixtures/'sky-planes-host-report.json').read_text());manifest=json.loads((build/'apk-build-report.json').read_text());payloads={}
for name,digest in host['source_sha256'].items():
 key=('tests' if name.endswith('Test.java') else 'java')+'/org/codex/nfsugpreview/'+name;assert manifest['source_sha256'][key]==digest
try:
 print(run(['install','-r',build/'NFSUG-Android-Core-Preview.apk']).decode(),flush=True);run(['shell','run-as','org.codex.nfsugpreview','mkdir','-p','files/sky-fixtures'])
 for path in [fixtures/'asset.bin',fixtures/'samples.tsv',fixtures/'sky-palettes.bin',fixtures/'planes.tsv',*sorted(fixtures.glob('pair-*.bin'))]:
  name=path.name;digest=hashlib.sha256(path.read_bytes()).hexdigest();payloads[name]=digest;temp='/data/local/tmp/nfsug-sky-'+name;private='files/sky-fixtures/'+name
  try:run(['push',path,temp]);run(['shell','run-as','org.codex.nfsugpreview','cp',temp,private])
  finally:run(['shell','rm','-f',temp])
  assert run(['exec-out','run-as','org.codex.nfsugpreview','sha256sum',private]).decode().split()[0]==digest
 text=run(['shell','am','instrument','-w','-r','org.codex.nfsugpreview/.SkyGpuInstrumentation'],120).decode();(build/'sky-gpu-run.log').write_text(text);print(text,flush=True);assert 'PASS_ANDROID_SKY_GPU' in text and 'INSTRUMENTATION_CODE: -1' in text
 report=json.loads(run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/sky-gpu-report.json']));assert report['samples']==330 and report['pixel_checks']==54182400 and report['fractional_samples']>0;report['fixtures']=payloads;report['apk_sha256']=manifest['sha256'];(build/'sky-gpu-android-report.json').write_text(json.dumps(report,indent=2))
finally:
 (build/'sky-gpu-logcat.log').write_bytes(run(['logcat','-d','-t','2000']))
 for name in payloads:run(['shell','run-as','org.codex.nfsugpreview','rm','-f','files/sky-fixtures/'+name])
 print(run(['install','-r',root/'tryout/NFSUG-Android-Core-Preview-20261015-LifecycleUpdate/NFSUG-Android-Core-Preview.apk']).decode(),flush=True);run(['emu','kill'])

