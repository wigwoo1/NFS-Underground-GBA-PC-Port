from pathlib import Path
import hashlib,json,subprocess,time,argparse
parser=argparse.ArgumentParser();parser.add_argument('--app',type=Path);args=parser.parse_args()
b=Path(r'C:\NFSUG-Workspace');r=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');app=args.app or b/'NFSUG-android-local/app-preview-ui-tests';adb=b/'android-tools/sdk/platform-tools/adb.exe';fixtures=b/'NFSUG-complete-scene-gpu-fixtures'
def run(args,timeout=45):return subprocess.run([str(adb),'-s','emulator-5556',*map(str,args)],check=True,capture_output=True,timeout=timeout).stdout
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for i in range(60):
 try:
  if run(['shell','getprop','sys.boot_completed'],5).strip()==b'1':break
 except (subprocess.CalledProcessError,subprocess.TimeoutExpired):pass
 time.sleep(1)
else:raise RuntimeError('Owned emulator not booted')
assert run(['emu','avd','name']).decode().splitlines()[0].strip()=='NFSUG_API30'
a=json.loads((app/'apk-build-report.json').read_text());assert sha(Path(a['apk']))==a['sha256']
for name,digest in a['source_sha256'].items():assert sha(r/'work/android'/name)==digest,name
restore=r/'tryout/NFSUG-Android-Core-Preview-20261015-LifecycleUpdate/NFSUG-Android-Core-Preview.apk';restore_sha='8c901a522176955ec8592a961766dead26ab7275de81a0e01a3b1de790bc383f';assert sha(restore)==restore_sha
inputs={name:sha(fixtures/name) for name in ('background-test.gba','background-test.state')};owned=[];installed=False
try:
 run(['install','-r',a['apk']]);installed=True;print('Test APK installed',flush=True)
 for name,digest in inputs.items():
  dest='files/'+name;temp='/data/local/tmp/nfsug-'+name;owned.append(dest)
  try:run(['push',fixtures/name,temp]);run(['shell','run-as','org.codex.nfsugpreview','cp',temp,dest])
  finally:run(['shell','rm','-f',temp])
  assert run(['exec-out','run-as','org.codex.nfsugpreview','sha256sum',dest]).decode().split()[0]==digest
 run(['logcat','-c']);output=run(['shell','am','instrument','-w','-r','org.codex.nfsugpreview/.PreviewNativeUiInstrumentation'],240).decode();(app/'preview-native-ui-instrumentation.log').write_text(output);print(output,flush=True);(app/'preview-native-ui-logcat.txt').write_bytes(run(['logcat','-d','-v','threadtime']))
 try:
  run(['shell','run-as','org.codex.nfsugpreview','test','-f','files/preview-native-ui.png']);(app/'preview-native-ui.png').write_bytes(run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/preview-native-ui.png']));owned.append('files/preview-native-ui.png')
 except subprocess.CalledProcessError:pass
 assert 'PASS_ANDROID_PREVIEW_NATIVE_UI' in output and 'INSTRUMENTATION_CODE: -1' in output
 report=json.loads(run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/preview-native-ui-report.json']));owned.append('files/preview-native-ui-report.json');report['apk_sha256']=a['sha256'];report['fixtures']=inputs;(app/'preview-native-ui-android-report.json').write_text(json.dumps(report,indent=2))
finally:
 run(['shell','am','force-stop','org.codex.nfsugpreview']);assert run(['emu','avd','name']).decode().splitlines()[0].strip()=='NFSUG_API30'
 cleanup=[]
 if installed:
  for dest in owned:
   try:run(['shell','run-as','org.codex.nfsugpreview','rm','-f',dest])
   except Exception as failure:cleanup.append(str(failure))
  for name in ('game.gba','resume.state','resume.state.bak','resume.state.new','battery.sav','battery.sav.bak','battery.sav.new'):
   try:run(['shell','run-as','org.codex.nfsugpreview','rm','-f','files/preview-ui-test-private/'+name])
   except Exception as failure:cleanup.append(str(failure))
  # Exact named directory; no recursive removal of unexpected files.
  exists=subprocess.run([str(adb),'-s','emulator-5556','shell','run-as','org.codex.nfsugpreview','test','-d','files/preview-ui-test-private'],capture_output=True).returncode==0
  if exists:
   try:run(['shell','run-as','org.codex.nfsugpreview','rmdir','files/preview-ui-test-private'])
   except Exception as failure:cleanup.append(str(failure))
 run(['install','-r',restore]);path=run(['shell','pm','path','org.codex.nfsugpreview']).decode().strip().split(':',1)[1];assert run(['shell','sha256sum',path]).decode().split()[0]==restore_sha;print('Published APK restored and installed hash verified',flush=True);run(['emu','kill'])

 if cleanup:raise RuntimeError('Named test cleanup failed: '+str(cleanup))

