from pathlib import Path
import subprocess,json,hashlib,time
base=Path(r'C:\NFSUG-Workspace');root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');build=base/'NFSUG-android-local/app-retained-sequence-gpu-tests';fixtures=base/'NFSUG-android-source-road-sequence-local';adb=base/'android-tools/sdk/platform-tools/adb.exe'
def run(args,timeout=45):return subprocess.run([str(adb),'-s','emulator-5556',*map(str,args)],check=True,capture_output=True,timeout=timeout).stdout
for i in range(60):
 try:
  if run(['shell','getprop','sys.boot_completed'],5).strip()==b'1':break
 except (subprocess.CalledProcessError,subprocess.TimeoutExpired):pass
 time.sleep(1)
else:raise RuntimeError('Owned emulator not booted')
assert run(['emu','avd','name']).decode().splitlines()[0].strip()=='NFSUG_API30'
manifest=json.loads((build/'apk-build-report.json').read_text());capture=json.loads((fixtures/'source-fixture-capture-report.json').read_text());assets=[];files=[name for entry in capture['fixtures'].values() for name in (entry['filename'],f"background-{entry['refresh']}.rgba")]+['road-candidates.bin','original-road-events.nrj']+[path.name for path in fixtures.glob('owner-*.nrp')]+[path.name for path in fixtures.glob('retention-*.ref')];payloads={}
try:
 run(['install','-r',build/'NFSUG-Android-Core-Preview.apk']);run(['shell','run-as','org.codex.nfsugpreview','mkdir','-p','files/sequence-scene-fixtures'])
 for name in files:
  path=fixtures/name;digest=hashlib.sha256(path.read_bytes()).hexdigest()
  for a in assets:
   if a['filename']==name:assert digest==a['sha256']
  temp='/data/local/tmp/nfsug-edge-'+name;private='files/sequence-scene-fixtures/'+name
  try:run(['push',path,temp]);run(['shell','run-as','org.codex.nfsugpreview','cp',temp,private])
  finally:run(['shell','rm','-f',temp])
  assert run(['exec-out','run-as','org.codex.nfsugpreview','sha256sum',private]).decode().split()[0]==digest;payloads[name]=digest
 text=run(['shell','am','instrument','-w','-r','org.codex.nfsugpreview/.RetainedSequenceGpuInstrumentation'],180).decode();(build/'retained-sequence-gpu-run.log').write_text(text);print(text,flush=True);assert 'PASS_ANDROID_RETAINED_SEQUENCE_GPU' in text and 'INSTRUMENTATION_CODE: -1' in text
 report=json.loads(run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/retained-sequence-gpu-report.json']));assert report['coverage_holes']==0 and report['retained_source_color_checks']>650000 and report['snapshots']==49 and report['coverage_checks']==1920000 and report['pixel_checks']>1920000;report['fixtures']=payloads;report['apk_sha256']=manifest['sha256'];(build/'retained-sequence-gpu-android-report.json').write_text(json.dumps(report,indent=2))
finally:
 for name in payloads:run(['shell','run-as','org.codex.nfsugpreview','rm','-f','files/sequence-scene-fixtures/'+name])
 run(['install','-r',root/'tryout/NFSUG-Android-Core-Preview-20261015-LifecycleUpdate/NFSUG-Android-Core-Preview.apk']);run(['emu','kill'])
