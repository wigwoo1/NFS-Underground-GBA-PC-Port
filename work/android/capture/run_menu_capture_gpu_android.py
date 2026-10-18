from pathlib import Path
import subprocess,json,hashlib,time
base=Path(r'C:\NFSUG-Workspace');root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');build=base/'NFSUG-android-local/app-menu-capture-gpu-tests';adb=base/'android-tools/sdk/platform-tools/adb.exe'
def run(args,timeout=60):return subprocess.run([str(adb),'-s','emulator-5556',*map(str,args)],check=True,capture_output=True,timeout=timeout).stdout
for i in range(60):
 try:
  if run(['shell','getprop','sys.boot_completed'],5).strip()==b'1':break
 except (subprocess.CalledProcessError,subprocess.TimeoutExpired):pass
 time.sleep(1)
else:raise RuntimeError('Emulator not ready')
assert run(['emu','avd','name']).decode().splitlines()[0].strip()=='NFSUG_API30'
try:
 print(run(['install','-r',build/'NFSUG-Android-Core-Preview.apk']).decode(),flush=True)
 for name,path in {'menu-capture.gba':root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba','menu-capture.state':root/'work/fix-menu/menu-4.state'}.items():
  temp='/data/local/tmp/nfsug-'+name;private='files/'+name;digest=hashlib.sha256(path.read_bytes()).hexdigest()
  try:run(['push',path,temp]);run(['shell','run-as','org.codex.nfsugpreview','cp',temp,private])
  finally:run(['shell','rm','-f',temp])
  assert run(['exec-out','run-as','org.codex.nfsugpreview','sha256sum',private]).decode().split()[0]==digest
 text=run(['shell','am','instrument','-w','-r','org.codex.nfsugpreview/.MenuCaptureGpuInstrumentation'],180).decode();(build/'menu-capture-gpu-run.log').write_text(text);print(text,flush=True);assert 'PASS_ANDROID_DYNAMIC_MENU_CAPTURE_GPU' in text and 'INSTRUMENTATION_CODE: -1' in text
 report=json.loads(run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/menu-capture-gpu-report.json']));report['apk_sha256']=json.loads((build/'apk-build-report.json').read_text())['sha256'];(build/'menu-capture-gpu-android-report.json').write_text(json.dumps(report,indent=2))
finally:
 for name in ('menu-capture.gba','menu-capture.state'):run(['shell','run-as','org.codex.nfsugpreview','rm','-f','files/'+name])
 print(run(['install','-r',root/'tryout/NFSUG-Android-Core-Preview-20261015-LifecycleUpdate/NFSUG-Android-Core-Preview.apk']).decode(),flush=True);run(['emu','kill'])
