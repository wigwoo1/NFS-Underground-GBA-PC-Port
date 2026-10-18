"""Current normal write-ownership capture, native build receipts and real consumer verification."""
from pathlib import Path
import hashlib,json,subprocess,shutil
r=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');b=Path(r'C:\NFSUG-Workspace');out=b/'NFSUG-write-owner-api-fixtures';native=b/'NFSUG-android-write-owner-native-local';fixtures=b/'NFSUG-wall-assets-fixtures'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
run=json.loads((out/'write-owner-api-report.json').read_text());default=json.loads((out/'default-off-regression.json').read_text());component=json.loads((b/'NFSUG-write-owner-component-local/component-report.json').read_text());build=json.loads((native/'capture-jni-build-report.json').read_text());source=json.loads((native/'source-provenance.json').read_text())
assert run['proof_cells']==499200 and run['older_proof_checks']==147 and run['wall_owners']==148 and run['source_writer_checks']==299970 and run['post_reset_original_frames']==80
assert default['endpoint_packets']==148 and default['all_packet_bytes_equal'] and component['cell_kind_and_refresh_checks']==844800
for name,digest in component['source_hashes'].items():assert sha(r/name)==digest,name
for name,digest in source['unaltered_source_sha256'].items():assert sha(r/('outputs/nfsug-research' if name in ('native_span.c','native_span.h') else 'work')/name)==digest,name
for name,digest in build['native_inputs'].items():
 if name.endswith(('.c','.h','.inc','CMakeLists.txt','/build_capture.py','/stage_capture.py')):assert sha(r/name)==digest,name
for target in build['targets']:
 lib=native/target['library'];assert sha(lib)==target['sha256'];symbols=subprocess.run([str(b/'android-tools/android-ndk-r30/toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-readelf.exe'),'--dyn-syms','--wide',str(lib)],check=True,capture_output=True,text=True).stdout;assert 'nfa_core_capture_write_ownership' in symbols
wall_files=list(out.glob('owner-*.nwh'));assert len(wall_files)==13
for p in wall_files:assert p.read_bytes()==(b/'NFSUG-wall-owner-api-fixtures'/p.name).read_bytes(),p.name
capture=json.loads((fixtures/'source-fixture-capture-report.json').read_text())
for entry in capture['fixtures'].values():
 for name in (entry['filename'],f"wall-retention-{entry['refresh']}.ref"):shutil.copyfile(fixtures/name,out/name)
jdk=b/'android-tools/jdk-21.0.12.1+1/bin';classes=out/'frozen-classes';test=r/'work/android/tests/org/codex/nfsugpreview/FrozenWallRetentionTest.java'
subprocess.run([str(jdk/'javac.exe'),'--release','8','-sourcepath',str(r/'work/android/java'),'-d',str(classes),str(test)],check=True)
text=subprocess.run([str(jdk/'java.exe'),'-cp',str(classes),'org.codex.nfsugpreview.FrozenWallRetentionTest',str(out),str(out)],check=True,capture_output=True,text=True).stdout.strip();assert 'PASS_FROZEN_WALL_RETENTION' in text
report=dict(result='PASS_NORMAL_SOURCE_WRITE_OWNERSHIP',original_frames=600,post_reset_original_frames=80,original_timing_audio=True,completed_owners=148,source_proof_cells=499200,older_proof_immutable_checks=147,component_cells=844800,wall_source_writer_checks=299970,default_packets_equal=148,wall_snapshot_bytes_identical=13,normal_proof_wall_consumer=text,source_and_native_hashes_verified=True,android_runtime=False,live_renderer=False,source_hashes={name:sha(r/name) for name in ['work/camera/write_ownership.c','work/camera/write_ownership.h','work/camera/world_trace.h','work/android/capture/observer_adapter.inc','work/android/capture/core_capture_api.inc','work/android/capture/nfsug_capture.h','work/android/capture/test_write_ownership_component_host.py','work/android/capture/test_write_owner_api_host.py','work/android/capture/test_write_capture_default_host.py','work/android/capture/verify_write_owner_host.py']})
(out/'write-owner-integration-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='source_hashes'},indent=2))

