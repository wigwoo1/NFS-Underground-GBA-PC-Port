"""Package source-bound limited Android native preview; preserve existing tryouts."""
from pathlib import Path
import hashlib,json,shutil,zipfile
source=Path(__file__).resolve().parent;root=source.parents[1];base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-Android-Native-Current-20261017';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
b=json.loads((out/'production/apk-build-report.json').read_text());t=json.loads((out/'ui-test/apk-build-report.json').read_text());r=json.loads((out/'ui-results/current-native-ui-report.json').read_text());n=json.loads((out/'native/capture-jni-build-report.json').read_text())
assert b['result']=='PASS_SIGNED_APK_BUILD' and b['native_capture'] and not b['instrumentation'] and not b['rom_bundled'] and not b['private_key_bundled']
assert r['result']=='PASS_ANDROID_PREVIEW_NATIVE_UI' and r['production_java_and_native_match'] and r['native_presentations']>0 and r['event_assertions']==38
assert r['production_apk_sha256']==b['sha256']==sha(out/'production/NFSUG-Android-Core-Preview.apk') and r['instrumentation_apk_sha256']==t['sha256']
assert r['runner_sha256']==sha(source/'run_current_native_ui.py') and not r['complete_race'] and not r['full_scene_60fps']
for name,h in b['source_sha256'].items():assert sha(source/name)==h,name
for name,h in t['source_sha256'].items():assert sha(source/name)==h,name
for name,h in n['native_inputs'].items():
 if name.endswith(('.c','.h','.inc','CMakeLists.txt','/stage_capture.py','/build_capture.py')):assert sha(root/name)==h,name
with zipfile.ZipFile(out/'production/NFSUG-Android-Core-Preview.apk') as z:
 for target in n['targets']:assert hashlib.sha256(z.read('lib/'+target['abi']+'/libnfsug_android_core.so')).hexdigest()==target['sha256']
 assert not any(x.lower().endswith(('.gba','.sav','.state','.jks','.p12')) for x in z.namelist())
dest=root/'tryout'/('NFSUG-Android-Native-Preview-20261017-'+b['sha256'][:8]);dest.mkdir(exist_ok=False)
apk=dest/'NFSUG-Android-Native-Preview.apk';shutil.copy2(out/'production/NFSUG-Android-Core-Preview.apk',apk);assert sha(apk)==b['sha256']
for label,path in [('apk-build-report.json',out/'production/apk-build-report.json'),('native-build-report.json',out/'native/capture-jni-build-report.json'),('native-source-provenance.json',out/'native/source-provenance.json'),('live-ui-test-report.json',out/'ui-results/current-native-ui-report.json'),('signature-verify.log',out/'production/signature-verify.log'),('alignment-verify.log',out/'production/alignment-verify.log'),('preview-native-ui.png',out/'ui-results/preview-native-ui.png')]:shutil.copy2(path,dest/label)
(dest/'READ ME.txt').write_text("""NFS Underground Android native-renderer EXPERIMENTAL preview

1. Copy NFSUG-Android-Native-Preview.apk to your Android device and install it.
2. Open the app, choose OPEN ROM and select your supplied USA/Europe .gba ROM.
3. Menus and unavailable native scenes use the original display. During a race,
   tap NATIVE to try the experimental native scene renderer. Tap it again to
   return to the original display. D-pad, A, B, Start and Select are onscreen.
4. PAUSE / RESUME pauses the game. Home also pauses it and releases touch input.

This APK includes both arm64-v8a and x86_64 libraries; Android 8/API26 or later.
No ROM, save, checkpoint or signing key is bundled. Game logic still uses mGBA.
Native rendering uses the original textures. No upscaled 4K texture option yet.
The app label may still say Core Preview; native capture is enabled in this APK.

Verified: matching production/test Java and native libraries; emulator boot,
moving native checkpoint scene, renderer toggle, pause/recreation/resume,
38 touch assertions, shutdown; ordinary APK installs and launches. Separate
tests verified41 touch/recovery assertions and frozen native scenes at4K.

NOT verified: physical phone performance/touch/audio, full race, smooth60-fps
full-scene/sky motion, all game scenes or complete original-image fidelity.
This is not a completed standalone game-code rewrite or a PC audio fix.
If it performs badly, turn NATIVE off. Report your device model, Android version,
where the issue occurs, and whether it happens with NATIVE on or off.

Existing app-private saves are preserved by same-key updates; uninstalling or
clearing app data deletes them. Keep older preview packages for comparison.
""",encoding='utf8')
manifest=dict(result='PACKAGED_LIMITED_ANDROID_NATIVE_RENDERER_PREVIEW',apk_sha256=sha(apk),native_capture_enabled=True,emulator_live_ui_verified=True,production_install_launch_verified=True,physical_device_verified=False,full_race_verified=False,full_scene_60fps=False,original_game_logic='mGBA',rough_project_percent=72,files_sha256={x.name:sha(x) for x in dest.iterdir() if x.is_file()},packager_sha256=sha(Path(__file__)))
(dest/'package-manifest.json').write_text(json.dumps(manifest,indent=2));print(str(dest));print(json.dumps(manifest,indent=2))
