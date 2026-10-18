from pathlib import Path
import hashlib,json,zipfile,subprocess,struct
r=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');b=Path(r'C:\NFSUG-Workspace');test=b/'NFSUG-android-local/app-preview-ui-tests';release=b/'NFSUG-android-local/app-native-experiment-release';native=b/'NFSUG-android-background-jni-native-local'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
t=json.loads((test/'apk-build-report.json').read_text());a=json.loads((release/'apk-build-report.json').read_text());v=json.loads((test/'preview-native-ui-android-report.json').read_text());n=json.loads((native/'capture-jni-build-report.json').read_text())
assert v['result']=='PASS_ANDROID_PREVIEW_NATIVE_UI' and v['event_assertions']==38 and v['native_presentations']>=3
for flag in ('ordinary_preview_activity_inherited','isolated_test_saves','boot_fallback','race_checkpoint_native_display','paused_activity_recreation','normal_exit_releases_core'):assert v[flag]
assert not v['physical_touch'] and not v['complete_race'] and not v['full_scene_60fps']
assert sha(Path(t['apk']))==t['sha256']==v['apk_sha256'] and sha(Path(a['apk']))==a['sha256'] and not a['instrumentation'] and a['result']=='PASS_SIGNED_APK_BUILD'
for report in (t,a):
 for name,digest in report['source_sha256'].items():assert sha(r/'work/android'/name)==digest,name
assert {k:v for k,v in t['source_sha256'].items() if k.startswith('java/')}=={k:v for k,v in a['source_sha256'].items() if k.startswith('java/')}
assert a['generated_build_config_sha256']==t['generated_build_config_sha256'] and a['native_capture']
for name,digest in n['native_inputs'].items():
 if name.endswith(('.c','.h','.inc','CMakeLists.txt','/stage_capture.py','/build_capture.py')):assert sha(r/name)==digest,name
for package in (t,a):
 with zipfile.ZipFile(package['apk']) as z:
  for target in n['targets']:assert hashlib.sha256(z.read('lib/'+target['abi']+'/libnfsug_android_core.so')).hexdigest()==target['sha256']
with zipfile.ZipFile(a['apk']) as z:
 dex=z.read('classes.dex')
 for name in ('FixturePreviewActivity','LiveTestActivity','PreviewNativeUiInstrumentation','LivePresentationInstrumentation'):assert name.encode() not in dex,name
assert len(v['fixtures'])==2
for name,digest in v['fixtures'].items():assert sha(b/'NFSUG-complete-scene-gpu-fixtures'/name)==digest
raw=(test/'preview-native-ui.png').read_bytes();assert raw[:8]==b'\x89PNG\r\n\x1a\n';size=struct.unpack_from('>II',raw,16);assert size[0]>size[1] and size[1]>=480
android=b/'android-tools';dump=subprocess.run([str(android/'sdk/build-tools/36.0.0/aapt2.exe'),'dump','xmltree','--file','AndroidManifest.xml',a['apk']],check=True,capture_output=True,text=True).stdout
assert 'instrumentation' not in dump.lower() and 'FixturePreviewActivity' not in dump and 'PreviewActivity' in dump
launch=json.loads((release/'release-launch-report.json').read_text());assert launch['result']=='PASS_RELEASE_EMULATOR_LAUNCH' and launch['apk_sha256']==a['sha256'] and launch['normal_rom_save_bytes_preserved'] and launch['published_apk_restored']
cert=subprocess.run([str(android/'jdk-21.0.12.1+1/bin/java.exe'),'-jar',str(android/'sdk/build-tools/36.0.0/lib/apksigner.jar'),'verify','--print-certs',a['apk']],check=True,capture_output=True,text=True).stdout
assert '011123f9ccc02df876129e51476ccffbbcf1b9b2f97a99327fd829f4faeb7b32' in cert
result=dict(result='PASS_PREVIEW_UI_AND_EXPERIMENTAL_RELEASE',release_installed_and_ordinary_entry_launched=True,published_signing_certificate_matches=True,touch_event_assertions=38,boot_fallback=True,race_checkpoint_native_display=True,paused_activity_recreation=True,normal_exit_releases_core=True,normal_java_and_generated_config_equal=True,source_apk_native_fixture_hashes_verified=True,instrumentation_absent_from_release=True,screenshot_size=size,screenshot_sha256=sha(test/'preview-native-ui.png'),test_apk_sha256=t['sha256'],release_apk_sha256=a['sha256'],physical_device=False,complete_menu_to_race_flow=False,full_race=False,full_scene_60fps=False,scope='Ordinary PreviewActivity inherited UI tested with isolated files directory; release built from identical normal Java/config/native libraries without instrumentation. Physical release installation untested.')
(release/'preview-ui-release-verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
