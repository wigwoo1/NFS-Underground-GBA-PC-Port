"""Verify normal wall owner API receipts, source provenance, native exports and Java decoding."""
from pathlib import Path
import hashlib,json,subprocess
root=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');base=Path(r'C:\NFSUG-Workspace');native=base/'NFSUG-android-wall-owner-native-local';out=base/'NFSUG-wall-owner-api-fixtures'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
runtime=json.loads((out/'wall-owner-api-report.json').read_text());default=json.loads((out/'default-off-regression.json').read_text());build=json.loads((native/'capture-jni-build-report.json').read_text());provenance=json.loads((native/'source-provenance.json').read_text())
assert runtime['wall_owners']==148 and runtime['source_writer_checks']==299970 and runtime['older_owner_immutable_checks']==147 and runtime['post_reset_original_frames']==80 and not runtime['diagnostic_setup_required']
assert default['endpoint_packets']==148 and default['all_packet_bytes_equal']
for name,digest in provenance['unaltered_source_sha256'].items():assert sha(root/('work' if name not in ('native_span.c','native_span.h') else 'outputs/nfsug-research')/name)==digest,name
for name,digest in build['native_inputs'].items():
 if name.endswith(('.c','.h','.inc','CMakeLists.txt','/stage_capture.py','/build_capture.py')):assert sha(root/name)==digest,name
for target in build['targets']:
 lib=native/target['library'];assert sha(lib)==target['sha256'];symbols=subprocess.run([str(base/'android-tools/android-ndk-r30/toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-readelf.exe'),'--dyn-syms','--wide',str(lib)],check=True,capture_output=True,text=True).stdout
 for name in ('nfa_core_capture_wall_history_enable','nfa_core_capture_wall_history','nfa_core_capture_wall_history_stats'):assert name in symbols
jdk=base/'android-tools/jdk-21.0.12.1+1/bin';classes=out/'classes';test=root/'work/android/tests/org/codex/nfsugpreview/BoundedWallHistoryTest.java'
subprocess.run([str(jdk/'javac.exe'),'--release','8','-sourcepath',str(root/'work/android/java'),'-d',str(classes),str(test)],check=True)
java=subprocess.run([str(jdk/'java.exe'),'-cp',str(classes),'org.codex.nfsugpreview.BoundedWallHistoryTest',str(out),str(base/'NFSUG-wall-assets-fixtures')],check=True,capture_output=True,text=True).stdout.strip()
result=dict(result='PASS_NORMAL_WALL_OWNER_API_INTEGRATION',java_result=java,source_hashes_verified=True,normal_core_api=True,original_frames=600,post_reset_original_frames=80,wall_owners=148,older_owner_checks=147,default_packets_equal=148,native_builds=build['targets'],android_runtime=False,jni_methods_exposed=False,live_renderer_connected=False,source_hashes={name:sha(root/name) for name in ['work/camera/world_trace.h','work/android/capture/observer_adapter.inc','work/android/capture/core_capture_api.inc','work/android/capture/nfsug_capture.h','work/android/capture/test_wall_owner_api_host.py','work/android/capture/test_wall_capture_default_host.py','work/android/capture/verify_wall_owner_api_host.py']})
(out/'wall-owner-integration-report.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ('source_hashes','native_builds')},indent=2))
