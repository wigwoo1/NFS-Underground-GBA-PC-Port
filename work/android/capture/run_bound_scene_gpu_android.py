from pathlib import Path
import subprocess,json,hashlib,time
base=Path(r'C:\NFSUG-Workspace');root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');build=base/'NFSUG-android-local/app-bound-scene-gpu-tests';fixtures=base/'NFSUG-android-source-road-assets-local';adb=base/'android-tools/sdk/platform-tools/adb.exe'
def run(args,timeout=45):return subprocess.run([str(adb),'-s','emulator-5556',*map(str,args)],check=True,capture_output=True,timeout=timeout).stdout
for i in range(60):
 try:
  if run(['shell','getprop','sys.boot_completed'],5).strip()==b'1':break
 except (subprocess.CalledProcessError,subprocess.TimeoutExpired):pass
 time.sleep(1)
else:raise RuntimeError('Owned emulator not booted')
assert run(['emu','avd','name']).decode().splitlines()[0].strip()=='NFSUG_API30'
manifest=json.loads((build/'apk-build-report.json').read_text());payloads={}

try:
 print(run(['install','-r',build/'NFSUG-Android-Core-Preview.apk']).decode(),flush=True);run(['shell','run-as','org.codex.nfsugpreview','mkdir','-p','files/bound-scene-fixtures'])
 for path in [fixtures/filename for kind in ('whole','split') for filename in ('race-background-'+kind+'.nrb','background-'+kind+'.rgba')]+[fixtures/'road-candidates.bin']:
  name=path.name;digest=hashlib.sha256(path.read_bytes()).hexdigest();kind='whole' if 'whole' in name else 'split';key='snapshot_sha256' if path.suffix=='.nsb' else 'rgba_sha256';payloads[name]=digest;temp='/data/local/tmp/nfsug-sky-'+name;private='files/bound-scene-fixtures/'+name
  try:run(['push',path,temp]);run(['shell','run-as','org.codex.nfsugpreview','cp',temp,private])
  finally:run(['shell','rm','-f',temp])
  assert run(['exec-out','run-as','org.codex.nfsugpreview','sha256sum',private]).decode().split()[0]==digest
 text=run(['shell','am','instrument','-w','-r','org.codex.nfsugpreview/.BoundSceneGpuInstrumentation'],120).decode();(build/'bound-scene-gpu-run.log').write_text(text);print(text,flush=True);assert 'PASS_ANDROID_BOUND_ROAD_SCENE_GPU' in text and 'INSTRUMENTATION_CODE: -1' in text
 report=json.loads(run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/bound-scene-gpu-report.json']));assert report['coverage_checks']==115200 and report['coverage_holes']==0 and report['captured_endpoint_union_complete'] and report['pixel_checks']==633600 and report['object_samples']>0 and report['changed_background_samples']>0;report['fixtures']=payloads;report['apk_sha256']=manifest['sha256'];(build/'bound-scene-gpu-android-report.json').write_text(json.dumps(report,indent=2))
 for kind in ('whole','split'):
  for size in ('native','4k'):
   name='race-'+kind+'-'+size+'.png';(build/name).write_bytes(run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/'+name]))
finally:
 for name in payloads:run(['shell','run-as','org.codex.nfsugpreview','rm','-f','files/bound-scene-fixtures/'+name])
 print(run(['install','-r',root/'tryout/NFSUG-Android-Core-Preview-20261015-LifecycleUpdate/NFSUG-Android-Core-Preview.apk']).decode(),flush=True);run(['emu','kill'])
