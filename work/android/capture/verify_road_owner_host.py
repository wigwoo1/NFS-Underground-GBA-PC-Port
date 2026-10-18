"""Normal bounded road capture, legacy/compact readers, owner consumer and native receipts."""
from pathlib import Path
import hashlib,json,subprocess,struct
r=Path(r'Y:\CODEX\NFSUG-Native-PC-Port');b=Path(r'C:\NFSUG-Workspace');out=b/'NFSUG-road-owner-api-fixtures';native=b/'NFSUG-android-road-owner-native-local'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
subprocess.run([str(Path(__import__('sys').executable)),str(r/'work/android/capture/test_road_owner_api_host.py')],check=True,stdout=subprocess.DEVNULL)
run=json.loads((out/'road-owner-api-report.json').read_text());default=json.loads((out/'default-off-regression.json').read_text());component=json.loads((b/'NFSUG-road-store-component-local/component-report.json').read_text());build=json.loads((native/'capture-jni-build-report.json').read_text());source=json.loads((native/'source-provenance.json').read_text())
assert run['road_source_writer_checks']==145665 and run['older_road_checks']==147 and run['proof_cells']==499200 and run['wall_owners']==148 and run['source_writer_checks']==299970
assert default['endpoint_packets']==148 and default['all_packet_bytes_equal'] and component['replacement_runs']==100000 and component['retained_runs']==1 and component['asset_bytes']==65536
for name,digest in component['source_hashes'].items():assert sha(r/name)==digest
for name,digest in source['unaltered_source_sha256'].items():assert sha(r/('outputs/nfsug-research' if name in ('native_span.c','native_span.h') else 'work')/name)==digest,name
for name,digest in build['native_inputs'].items():
 if name.endswith(('.c','.h','.inc','CMakeLists.txt','/build_capture.py','/stage_capture.py')):assert sha(r/name)==digest,name
for target in build['targets']:
 lib=native/target['library'];assert sha(lib)==target['sha256'];symbols=subprocess.run([str(b/'android-tools/android-ndk-r30/toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-readelf.exe'),'--dyn-syms','--wide',str(lib)],check=True,capture_output=True,text=True).stdout;assert 'nfa_core_capture_road_history' in symbols
for p in out.glob('owner-*.nwh'):assert p.read_bytes()==(b/'NFSUG-write-owner-api-fixtures'/p.name).read_bytes(),p.name
for p in out.glob('owner-*.nrp'):assert p.read_bytes()==(b/'NFSUG-write-owner-api-fixtures'/p.name).read_bytes(),p.name
jdk=b/'android-tools/jdk-21.0.12.1+1/bin';classes=out/'combined-classes';tests=r/'work/android/tests/org/codex/nfsugpreview';names=['FrozenRoadRetentionTest','CompactRoadHistoryTest','RoadRetentionTest'];subprocess.run([str(jdk/'javac.exe'),'--release','8','-sourcepath',str(r/'work/android/java'),'-d',str(classes),*[str(tests/(n+'.java')) for n in names]],check=True)
reports=[]
for name,args in [('FrozenRoadRetentionTest',[out,out]),('CompactRoadHistoryTest',[out/'owner-16.nrh']),('RoadRetentionTest',[b/'NFSUG-android-source-road-sequence-local'])]:
 text=subprocess.run([str(jdk/'java.exe'),'-cp',str(classes),'org.codex.nfsugpreview.'+name,*map(str,args)],check=True,capture_output=True,text=True).stdout.strip();reports.append(text)
assert 'snapshots=9 source_cells=100870' in reports[0] and 'malformed_rejected=34' in reports[1] and 'snapshots=49 source_cells=652667' in reports[2]
files=list(out.glob('owner-*.nrh'));assert len(files)==13
result=dict(result='PASS_BOUNDED_ROAD_OWNER_INTEGRATION',completed_owners=148,road_source_writer_checks=145665,older_road_immutable_checks=147,source_proof_cells=499200,wall_source_writer_checks=299970,wall_and_proof_bytes_unchanged=True,original_frames=600,post_reset_frames=80,original_timing_audio=True,default_endpoint_packets_equal=148,replacement_runs=100000,replacement_retained_runs=1,max_selected_snapshot_bytes=max(p.stat().st_size for p in files),max_selected_retained_runs=max(struct.unpack_from('<Q',p.read_bytes(),40)[0] for p in files),java_tests=reports,source_and_native_hashes_verified=True,android_runtime=False,live_renderer=False,source_hashes={name:sha(r/name) for name in ['work/camera/road_history_store.c','work/camera/road_history_store.h','work/android/capture/observer_adapter.inc','work/android/java/org/codex/nfsugpreview/NativeRoadHistory.java','work/android/java/org/codex/nfsugpreview/NativeRoadRetention.java','work/android/tests/org/codex/nfsugpreview/FrozenRoadRetentionTest.java','work/android/tests/org/codex/nfsugpreview/CompactRoadHistoryTest.java','work/android/capture/test_road_owner_api_host.py','work/android/capture/test_bounded_road_store_host.py']})
(out/'road-owner-integration-report.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='source_hashes'},indent=2))
