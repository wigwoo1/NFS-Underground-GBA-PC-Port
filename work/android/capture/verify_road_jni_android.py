"""Current Android road/proof JNI and live-core retained-source consumer verification."""
from pathlib import Path
import hashlib,json,zipfile,subprocess
b=Path(r'C:\NFSUG-Workspace');r=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');app=b/'NFSUG-android-local/app-road-jni-tests';native=b/'NFSUG-android-road-jni-native-local';runtime=json.loads((app/'road-jni-android-report.json').read_text());apk=json.loads((app/'apk-build-report.json').read_text());build=json.loads((native/'capture-jni-build-report.json').read_text());provenance=json.loads((native/'source-provenance.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(Path(apk['apk']))==apk['sha256']==runtime['apk_sha256']
for name,digest in apk['source_sha256'].items():assert sha(r/'work/android'/name)==digest,name
for name,digest in provenance['unaltered_source_sha256'].items():assert sha(r/('outputs/nfsug-research' if name in ('native_span.c','native_span.h') else 'work')/name)==digest,name
for name,digest in build['native_inputs'].items():
 if name.endswith(('.c','.h','.inc','CMakeLists.txt','/build_capture.py','/stage_capture.py')):assert sha(r/name)==digest,name
with zipfile.ZipFile(apk['apk']) as z:
 for target in build['targets']:
  assert hashlib.sha256(z.read('lib/'+target['abi']+'/libnfsug_android_core.so')).hexdigest()==target['sha256']
  text=subprocess.run([str(b/'android-tools/android-ndk-r30/toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-readelf.exe'),'--dyn-syms','--wide',str(native/target['library'])],check=True,capture_output=True,text=True).stdout
  for method in ('captureRoadHistoryNative','captureWriteOwnershipNative'):assert 'Java_org_codex_nfsugpreview_NativeCore_'+method in text
for name,digest in runtime['fixtures'].items():assert sha(b/'NFSUG-road-jni-fixtures'/name)==digest
assert runtime['result']=='PASS_ANDROID_ROAD_OWNERSHIP_JNI' and runtime['wall_owners']==148 and runtime['pc_identical_road_owners']==runtime['pc_identical_proof_owners']==runtime['pc_identical_wall_owners']==13
assert runtime['older_owner_immutable_checks']==147 and runtime['source_display_snapshots']==594 and runtime['whole']==481 and runtime['split']==113 and runtime['original_rgba_frames']==600 and runtime['post_reset_original_frames']==80 and runtime['audio_frames']==443007 and runtime['original_timing']
assert runtime['retained_display_checks']==9 and runtime['retained_road_cells']==100870 and runtime['retained_wall_cells']==206571
# Verify exact host inputs behind all three per-owner Android hash references.
lines=(b/'NFSUG-road-jni-fixtures/road-owners.txt').read_text().splitlines();assert len(lines)==13
for row in lines:
 serial,*hashes=row.split()
 for extension,digest in zip(('nwh','nrh','nrp'),hashes):assert sha(b/f'NFSUG-road-owner-api-fixtures/owner-{serial}.{extension}')==digest
result=dict(result='PASS_ANDROID_ROAD_PROOF_JNI_INTEGRATION',api=runtime['api'],completed_owners=148,pc_identical_wall_road_proof_owners=13,older_owner_checks_per_component=147,original_rgba_frames=600,post_reset_original_frames=80,original_timing_audio=True,source_display_snapshots=594,whole=481,split=113,actual_core_retained_displays=9,road_source_cells=100870,wall_source_cells=206571,reset_disable_thread_range_close_guards=True,source_fixture_apk_native_hashes_verified=True,test_apk_sha256=apk['sha256'],gpu_presented=False,physical_arm64=False,real_time_pacing=False,source_hashes={name:sha(r/name) for name in ['work/android/nfsug_android_jni.c','work/android/java/org/codex/nfsugpreview/NativeCore.java','work/android/java/org/codex/nfsugpreview/NativeRoadHistory.java','work/android/java/org/codex/nfsugpreview/NativeRoadRetention.java','work/android/instrumentation/org/codex/nfsugpreview/RoadHistoryInstrumentation.java','work/android/capture/verify_road_jni_android.py']})
(app/'road-jni-integration-report.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='source_hashes'},indent=2))
