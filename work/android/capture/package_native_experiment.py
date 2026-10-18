from pathlib import Path
import hashlib,json,shutil
r=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');b=Path(r'C:\NFSUG-Workspace');release=b/'NFSUG-android-local/app-native-experiment-release';test=b/'NFSUG-android-local/app-preview-ui-tests';out=r/'tryout/NFSUG-Android-Native-Experiment-20261015';out.mkdir(exist_ok=False)
report=json.loads((release/'preview-ui-release-verification.json').read_text());assert report['result']=='PASS_PREVIEW_UI_AND_EXPERIMENTAL_RELEASE'
shutil.copy2(release/'NFSUG-Android-Core-Preview.apk',out/'NFSUG-Android-Native-Experiment.apk');shutil.copy2(test/'preview-native-ui.png',out/'Native renderer screenshot.png');shutil.copy2(release/'preview-ui-release-verification.json',out/'verification.json');shutil.copy2(release/'release-launch-report.json',out/'launch-verification.json')
(out/'READ ME - Android.txt').write_text('''NFS UNDERGROUND - ANDROID NATIVE RENDERER EXPERIMENT
2026-10-15

An installable Android experiment with the original mGBA game core and an optional native scene renderer. This is not a completed standalone game-code port or the PC 4K fallback.

HOW TO TRY IT
1. Copy NFSUG-Android-Native-Experiment.apk and your supplied NFS Underground .gba ROM to your Android device. The ROM is not included.
2. Install the APK. Open "NFS Underground Core Preview".
3. Tap Open ROM and choose your supplied USA/Europe ROM.
4. Use the D-pad, A, B, START and SELECT. The original display is selected by default.
5. Enter a race, then tap Native: Off to enable the experimental native renderer. Native: On means the experiment is enabled; unsupported or incomplete scenes can still display the original image.
6. Tap Native: On to return to the original display. Pause / Resume pauses the app.

REQUIREMENTS
Android 8.0 or newer, ARM64 device with OpenGL ES 2.0. An x86_64 library is also included for Android emulators. Physical Android hardware has not yet been tested.

WHAT WAS VERIFIED
Actual Android API 30 emulator: ordinary app UI inherited in a test-only subclass with isolated saves; ROM boot/fallback, native race-checkpoint display, paused Activity recreation, native/original switching, 38 injected touch-event checks including multi-touch, Home/resume and normal worker shutdown. The release APK itself installed and opened its ordinary entry point on the emulator. Its normal Java code, native libraries and capture configuration match the UI-tested build. Test activities/instrumentation are absent from this APK. Signing certificate matches the existing published preview.

LIMITATIONS
Smooth 60-fps motion and real-time pacing are not verified. The software emulator is slow. A full race and the complete menu-to-race sequence have not been verified. Native camera/sky/object motion interpolation, Xbox/controller validation, original-vs-4K texture switching and upscaled UI/textures remain unfinished. Textures and HUD are currently original assets. Native geometry rendering does not mean the original game logic has been rewritten as standalone PC/Android code.

SAVES AND OTHER BUILDS
This package uses the existing preview app identity and signing key. Existing private save locations are retained. Supplied project ROMs/saves and the stable PC 4K fallback were not changed. Older published preview packages remain in their own folders.

Native renderer screenshot.png shows the actual tested app with native mode enabled. verification.json and launch-verification.json record the tested scope.
''',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(out/'NFSUG-Android-Native-Experiment.apk')==report['release_apk_sha256']
manifest={p.name:sha(p) for p in out.iterdir() if p.is_file()};(out/'SHA256.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(dict(result='PASS_EXPERIMENTAL_APK_PACKAGED',folder=str(out),apk_sha256=report['release_apk_sha256'],files=len(manifest)+1),indent=2))
