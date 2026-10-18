import hashlib,json,zipfile
from pathlib import Path
local=Path('C:/NFSUG-Workspace');root=Path('Y:/CODEX/NFSUG-Native-PC-Port/work/android');host_dir=local/'NFSUG-source-display-binding-fixtures';app=local/'NFSUG-android-local/app-source-display-jni-tests';native=local/'NFSUG-android-source-world-jni-local'
host=json.loads((host_dir/'host-binding-report.json').read_text());runtime=json.loads((app/'source-display-jni-android-report.json').read_text());build=json.loads((native/'capture-jni-build-report.json').read_text())
assert host['result']=='PASS_SOURCE_DISPLAY_BINDING_HOST' and host['forged_owner_rejections']==44
assert runtime['result']=='PASS_ANDROID_SOURCE_DISPLAY_JNI' and runtime['bound_display_snapshots']==594 and runtime['whole_snapshots']==481 and runtime['split_snapshots']==113 and runtime['bound_source_owners']==148
assert runtime['original_rgba_frames']==600 and runtime['original_timing'] and runtime['audio_pcm_frames']==443007 and runtime['historical_layers_provenance_unchanged']
stages=[p for p in app.glob('source-*') if p.is_dir()];assert len(stages)==1;stage=stages[0]
for name,digest in host['source_sha256'].items():
 prefix='tests' if name.startswith('World') else 'java';path=Path(prefix)/'org/codex/nfsugpreview'/name
 assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest and hashlib.sha256((stage/path).read_bytes()).hexdigest()==digest
assert hashlib.sha256((stage/'instrumentation/org/codex/nfsugpreview/SourceWorldInstrumentation.java').read_bytes()).hexdigest()==hashlib.sha256((root/'instrumentation/org/codex/nfsugpreview/SourceWorldInstrumentation.java').read_bytes()).hexdigest()
apk=app/'NFSUG-Android-Core-Preview.apk';assert hashlib.sha256(apk.read_bytes()).hexdigest()==runtime['test_apk_sha256']
with zipfile.ZipFile(apk) as archive:
 for target in build['targets']:assert hashlib.sha256(archive.read('lib/'+target['abi']+'/libnfsug_android_core.so')).hexdigest()==target['sha256']
report=dict(result='PASS_SOURCE_DISPLAY_BINDING_ANDROID_AND_HOST',display_snapshots=594,whole=481,split=113,source_owners=148,restored_owner_fixtures=host['restored_scene_owners'],host_forged_owner_rejections=44,historical_layers_provenance_unchanged=True,frame_timing_audio_original=True,source_and_apk_hashes_verified=True,immutable_bounded_cache=True,android_api=runtime['api'],test_apk_sha256=runtime['test_apk_sha256'],live_gpu_rendering=False,full_scene_60fps_gameplay=False)
(app/'source-display-integration-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
