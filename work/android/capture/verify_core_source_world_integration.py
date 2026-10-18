import hashlib,json,zipfile
from pathlib import Path
root=Path('Y:/CODEX/NFSUG-Native-PC-Port');local=Path('C:/NFSUG-Workspace');native=local/'NFSUG-android-source-world-jni-local';app=local/'NFSUG-android-local/app-source-world-jni-tests'
build=json.loads((native/'capture-jni-build-report.json').read_text());host=json.loads((native/'core-source-world-host-report.json').read_text());runtime=json.loads((app/'source-world-jni-android-report.json').read_text())
assert build['result']=='PASS_ANDROID_BORROWED_CAPTURE_BUILD' and build['visibility_capacity']==64 and build['jni']
assert host['result']=='PASS_CORE_SOURCE_WORLD_NO_ENV_REPLAY_LIFECYCLE' and host['source_packets']==148 and host['reset_replay_packets']==14
assert runtime['result']=='PASS_ANDROID_SOURCE_WORLD_JNI' and runtime['pc_identical_source_packets']==148 and runtime['original_rgba_frames']==600 and runtime['original_timing'] and runtime['audio_pcm_frames']==443007
for name in ('work/android/nfsug_android_jni.c','work/android/capture/core_capture_api.inc','work/android/capture/observer_adapter.inc','work/android/capture/nfsug_capture.h','work/android/capture/stage_capture.py'):
 assert hashlib.sha256((root/name).read_bytes()).hexdigest()==build['native_inputs'][name]
provenance=json.loads((native/'source-provenance.json').read_text())
for name in ('camera/live_visibility.h','camera/visibility_snapshot.c','camera/visibility_snapshot.h'):
 assert hashlib.sha256((root/'work'/name).read_bytes()).hexdigest()==provenance['unaltered_source_sha256'][name]
with zipfile.ZipFile(app/'NFSUG-Android-Core-Preview.apk') as apk:
 for target in build['targets']:
  assert hashlib.sha256(apk.read('lib/'+target['abi']+'/libnfsug_android_core.so')).hexdigest()==target['sha256']
  assert min(target['load_alignments'])>=16384 and not target['legacy_speed_apis_exported']
result=dict(result='PASS_CORE_AND_ANDROID_SOURCE_WORLD_LIFECYCLE',pc_replay=host['result'],android_runtime=runtime['result'],source_packets=148,original_frame_timing_audio_verified=True,reset_replay_packets=14,source_hashes_and_packaged_libraries_verified=True,diagnostic_environment_required=False,android_runtime_abi='x86_64',android_runtime_api=runtime['api'],arm64_build_verified=True,arm64_runtime_verified=False,live_gpu_rendering=False,full_scene_60fps_gameplay=False,apk_sha256=runtime['test_apk_sha256'],native_targets=build['targets'])
(native/'source-world-integration-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
