"""Bounded real-GPU and inherited live-preview checks; restores the prior preview."""
from pathlib import Path
import hashlib,json,subprocess,uuid,zipfile
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port')
base=Path(r'C:\NFSUG-Workspace')
out=base/'NFSUG-Android-Image-Reuse-20261017'
folder=out/'runtime-results';folder.mkdir(exist_ok=True)
adb=base/'android-tools/sdk/platform-tools/adb.exe'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(args,timeout=45):return subprocess.run([str(adb),'-s','emulator-5556']+args,check=True,capture_output=True,timeout=timeout).stdout
assert run(['emu','avd','name']).decode().splitlines()[0].strip()=='NFSUG_API30'
assert run(['shell','getprop','sys.boot_completed']).strip()==b'1'
test=out/'reuse-test/NFSUG-Android-Core-Preview.apk';production=out/'production/NFSUG-Android-Core-Preview.apk'
receipt=json.loads((test.parent/'apk-build-report.json').read_text())
assert sha(test)==receipt['sha256'] and receipt['runner']=='LiveImageReuseInstrumentation'
for name,h in receipt['source_sha256'].items():assert sha(root/'work/android'/name)==h,name
prod=json.loads((production.parent/'apk-build-report.json').read_text())
assert sha(production)==prod['sha256']
for name,h in prod['source_sha256'].items():
 if name.startswith('java/'):assert receipt['source_sha256'][name]==h,name
with zipfile.ZipFile(test) as a,zipfile.ZipFile(production) as b:
 for abi in ['x86_64','arm64-v8a']:
  key='lib/'+abi+'/libnfsug_android_core.so';assert a.read(key)==b.read(key)
restore=base/'NFSUG-Android-Core-Preview-SharedKey-20261017/NFSUG-Android-Core-Preview.apk'
restore_sha='4349f1a440e37e9b359aa25d34d98088ae202b198d7b15ce487cb6436d66256c';assert sha(restore)==restore_sha
gap=base/'NFSUG-Android-Traffic-20261017/gap3519-results'
witness=json.loads((gap/'first-gap-report.json').read_text());prefix='image-reuse-'+uuid.uuid4().hex[:12]
files={'owner0-kind0.bin':'background.bin','owner0-kind1.bin':'owner0-world.bin','owner0-kind2.bin':'owner0-road.bin','owner0-kind3.bin':'owner0-wall.bin','owner0-kind4.bin':'owner0-proof.bin'}
for name in files.values():assert sha(gap/name)==witness['frozen_component_sha256'][name]
protected={root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba':'53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593',root/'work/integration-0.state':'49e85564032a383626709b183f37aff34601c6e97cabdfcb17c117f72d996104'}
for path,h in protected.items():assert sha(path)==h
def push(path,name):
 temp='/data/local/tmp/'+prefix+'-'+name;run(['push',str(path),temp]);run(['shell','run-as','org.codex.nfsugpreview','cp',temp,'files/'+name]);run(['shell','rm',temp])
def instrument(runner,expected,report_name,args=None):
 output=run(['shell','am','instrument','-w','-r']+(args or [])+['org.codex.nfsugpreview/.'+runner],240).decode()
 (folder/(runner+'.log')).write_text(output,encoding='utf8');print(output,flush=True)
 assert expected in output and 'INSTRUMENTATION_CODE: -1' in output
 report=json.loads(run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/'+report_name]))
 report.update(test_apk_sha256=sha(test),production_apk_sha256=sha(production),production_java_native_matched=True,runner_sha256=sha(Path(__file__)))
 (folder/report_name).write_text(json.dumps(report,indent=2),encoding='utf8')
 return report
try:
 print(run(['install','-r',str(test)]).decode(),flush=True)
 for target,name in files.items():push(gap/name,prefix+'-'+target)
 run(['logcat','-c'])
 reuse=instrument('LiveImageReuseInstrumentation','PASS_ANDROID_EXACT_SCENE_IMAGE_REUSE',prefix+'-gpu-report.json',['-e','fixturePrefix',prefix])
 assert reuse['checks']['repeat_draws_skipped']==200 and reuse['checks']['actual_compositions']==6
 assert reuse['context_recreated'] and reuse['reference_pixels_exact'] and not reuse['full_scene_60fps']
 for path,name in zip(protected,['background-test.gba','background-test.state']):push(path,name)
 live=instrument('LivePresentationInstrumentation','PASS_ANDROID_LIVE_PRESENTATION','live-presentation-report.json')
 ui=instrument('PreviewNativeUiInstrumentation','PASS_ANDROID_PREVIEW_NATIVE_UI','preview-native-ui-report.json')
 assert ui['event_assertions']==38 and ui['normal_exit_releases_core']
 for path,h in protected.items():assert sha(path)==h
 summary=dict(result='PASS_REUSE_GPU_LIVE_UI_REGRESSIONS',gpu=reuse,live=live,ui=ui,full_scene_60fps=False,steady_state_performance=False,physical_device=False)
 (folder/'reuse-runtime-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
 print('PASS_REUSE_GPU_LIVE_UI_REGRESSIONS',flush=True)
finally:
 (folder/'runtime-logcat.txt').write_bytes(run(['logcat','-d','-v','threadtime']))
 run(['shell','am','force-stop','org.codex.nfsugpreview'])
 run(['install','-r',str(restore)])
 installed=run(['shell','pm','path','org.codex.nfsugpreview']).decode().strip().split(':',1)[1]
 assert run(['shell','sha256sum',installed]).decode().split()[0]==restore_sha
 print('Previous preview restored; installed APK hash exact',flush=True)
 assert run(['emu','avd','name']).decode().splitlines()[0].strip()=='NFSUG_API30'
 run(['emu','kill']);print('Owned emulator stopped',flush=True)
