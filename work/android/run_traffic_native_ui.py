"""Current native APK and inherited UI test, isolated fixture saves on owned emulator."""
from pathlib import Path
import hashlib,json,subprocess,time,uuid,zipfile
source=Path(__file__).resolve().parent;root=source.parents[1];base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-Android-Traffic-20261017';folder=out/'ui-results';folder.mkdir(exist_ok=True);adb=base/'android-tools/sdk/platform-tools/adb.exe';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(args,timeout=40):return subprocess.run([str(adb),'-s','emulator-5556']+args,check=True,capture_output=True,timeout=timeout)
terminal=out/'route-results/current-native-route-report.json';assert terminal.exists(),'Wait for SAME route session54477 terminal report before UI install'
assert json.loads(terminal.read_text())['all_original_pixels_audio_clocks_exact']
assert run(['emu','avd','name']).stdout.decode().splitlines()[0].strip()=='NFSUG_API30'
assert run(['shell','getprop','sys.boot_completed']).stdout.strip()==b'1'
test=json.loads((out/'ui-test/apk-build-report.json').read_text());production=json.loads((out/'production/apk-build-report.json').read_text());native=json.loads((out/'native/capture-jni-build-report.json').read_text())
assert test['instrumentation'] and test['runner']=='PreviewNativeUiInstrumentation' and production['native_capture'] and not production['instrumentation']
for name,h in test['source_sha256'].items():assert sha(source/name)==h,name
for name,h in production['source_sha256'].items():
 if name.startswith('java/'):assert test['source_sha256'][name]==h,name
assert test['generated_build_config_sha256']==production['generated_build_config_sha256']
for name in ['ui-test','production']:assert json.loads((out/name/'apk-build-report.json').read_text())['sha256']==sha(out/name/'NFSUG-Android-Core-Preview.apk')
with zipfile.ZipFile(out/'ui-test/NFSUG-Android-Core-Preview.apk') as left,zipfile.ZipFile(out/'production/NFSUG-Android-Core-Preview.apk') as right:
 for target in native['targets']:
  key='lib/'+target['abi']+'/libnfsug_android_core.so';assert hashlib.sha256(left.read(key)).hexdigest()==hashlib.sha256(right.read(key)).hexdigest()==target['sha256']
rom=root.parent/'Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba';state=root/'work/integration-0.state';before={str(p):sha(p) for p in [rom,state]};assert list(before.values())==['53817aec76a623dc2c7782ddf841f89f369aebe5a92a28c9afc69feaf914a593','49e85564032a383626709b183f37aff34601c6e97cabdfcb17c117f72d996104']
print(run(['install','-r',str(out/'ui-test/NFSUG-Android-Core-Preview.apk')]).stdout.decode(),flush=True)
prefix='native-current-'+uuid.uuid4().hex[:12]
for extension,path in [('gba',rom),('state',state)]:
 temporary='/data/local/tmp/'+prefix+'.'+extension;run(['push',str(path),temporary]);run(['shell','run-as','org.codex.nfsugpreview','cp',temporary,'files/'+prefix+'.'+extension]);run(['shell','rm',temporary])
run(['logcat','-c']);result=run(['shell','am','instrument','-w','-r','-e','fixturePrefix',prefix,'org.codex.nfsugpreview/.PreviewNativeUiInstrumentation'],timeout=240);text=result.stdout.decode();(folder/'instrumentation-run.log').write_text(text);print(text,flush=True)
(folder/'instrumentation-logcat.log').write_bytes(run(['logcat','-d','-s','NFSUGPreviewUI:E','AndroidRuntime:E','NFSUGPreview:I','*:S']).stdout)
assert 'PASS_ANDROID_PREVIEW_NATIVE_UI' in text and 'INSTRUMENTATION_CODE: -1' in text
r=json.loads(run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/preview-native-ui-report.json']).stdout);assert r['native_presentations']>0 and r['event_assertions']==38 and r['isolated_test_saves'] and r['normal_exit_releases_core'] and not r['full_scene_60fps']
(folder/'preview-native-ui.png').write_bytes(run(['exec-out','run-as','org.codex.nfsugpreview','cat','files/preview-native-ui.png']).stdout)
assert before=={str(p):sha(p) for p in [rom,state]}
r.update(production_apk_sha256=production['sha256'],instrumentation_apk_sha256=test['sha256'],native_libraries=native['targets'],fixture_prefix=prefix,rom_state_unchanged_sha256=before,production_java_and_native_match=True,source_bound_tests=True,runner_sha256=sha(Path(__file__)),scope='Owned API30 emulator boot/checkpoint UI, native moving endpoints/toggles/pause/recreation/touch. No full-race, original-clock cadence benchmark, physical Android device, audible quality, PC-audio fix or smooth60 proof.')
(folder/'current-native-ui-report.json').write_text(json.dumps(r,indent=2));print('VERIFIED_CURRENT_ANDROID_NATIVE_UI_LIMITED_PREVIEW',flush=True)
