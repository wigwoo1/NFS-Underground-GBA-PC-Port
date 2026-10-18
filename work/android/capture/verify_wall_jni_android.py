"""Join Android wall JNI runtime, current source/APK/native hashes and per-owner retention test."""
from pathlib import Path
import hashlib,json,zipfile,subprocess
b=Path(r'C:\NFSUG-Workspace');r=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');app=b/'NFSUG-android-local/app-wall-jni-tests';native=b/'NFSUG-android-wall-jni-native-local';runtime=json.loads((app/'wall-jni-android-report.json').read_text());apk=json.loads((app/'apk-build-report.json').read_text());build=json.loads((native/'capture-jni-build-report.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(Path(apk['apk']))==apk['sha256']==runtime['apk_sha256']
for name,digest in apk['source_sha256'].items():assert sha(r/'work/android'/name)==digest,name
for name,digest in build['native_inputs'].items():
 if name.endswith(('.c','.h','.inc','CMakeLists.txt','/build_capture.py','/stage_capture.py')):assert sha(r/name)==digest,name
with zipfile.ZipFile(apk['apk']) as z:
 for target in build['targets']:
  assert hashlib.sha256(z.read('lib/'+target['abi']+'/libnfsug_android_core.so')).hexdigest()==target['sha256']
  text=subprocess.run([str(b/'android-tools/android-ndk-r30/toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-readelf.exe'),'--dyn-syms','--wide',str(native/target['library'])],check=True,capture_output=True,text=True).stdout
  for method in ('captureWallHistoryEnableNative','captureWallHistoryNative','captureWallHistoryStatsNative'):assert 'Java_org_codex_nfsugpreview_NativeCore_'+method in text
for name,digest in runtime['fixtures'].items():assert sha(b/'NFSUG-wall-jni-fixtures'/name)==digest
assert runtime['result']=='PASS_ANDROID_WALL_HISTORY_JNI' and runtime['wall_owners']==148 and runtime['pc_identical_wall_owners']==13 and runtime['older_owner_immutable_checks']==147 and runtime['source_display_snapshots']==594 and runtime['whole']==481 and runtime['split']==113 and runtime['original_rgba_frames']==600 and runtime['post_reset_original_frames']==80 and runtime['audio_frames']==443007 and runtime['original_timing']
jdk=b/'android-tools/jdk-21.0.12.1+1/bin';classes=app/'frozen-host-classes';test=r/'work/android/tests/org/codex/nfsugpreview/FrozenWallRetentionTest.java'
subprocess.run([str(jdk/'javac.exe'),'--release','8','-sourcepath',str(r/'work/android/java'),'-d',str(classes),str(test)],check=True)
text=subprocess.run([str(jdk/'java.exe'),'-cp',str(classes),'org.codex.nfsugpreview.FrozenWallRetentionTest',str(b/'NFSUG-wall-assets-fixtures'),str(b/'NFSUG-wall-owner-api-fixtures')],check=True,capture_output=True,text=True).stdout.strip();assert 'PASS_FROZEN_WALL_RETENTION' in text
report=dict(result='PASS_WALL_JNI_AND_FROZEN_RETENTION',api=runtime['api'],wall_owners=148,pc_identical_owners=13,older_owner_checks=147,original_rgba_frames=600,post_reset_original_frames=80,source_display_snapshots=594,whole=481,split=113,original_timing_audio=True,source_and_packaged_native_hashes_verified=True,frozen_retention_host=text,test_apk_sha256=apk['sha256'],live_gpu=False,physical_arm64=False,real_time_pacing=False,source_hashes={name:sha(r/name) for name in ['work/android/nfsug_android_jni.c','work/android/java/org/codex/nfsugpreview/NativeCore.java','work/android/java/org/codex/nfsugpreview/NativeWallRetention.java','work/android/tests/org/codex/nfsugpreview/FrozenWallRetentionTest.java','work/android/instrumentation/org/codex/nfsugpreview/WallHistoryInstrumentation.java']})
(app/'wall-jni-integration-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='source_hashes'},indent=2))
