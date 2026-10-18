from pathlib import Path
import hashlib,json,subprocess
source=Path(__file__).parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-source-frame-tests';native=base/'NFSUG-android-background-jni-native-local'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((out/'build-report.json').read_text());component=json.loads((out/'component-report.json').read_text());live=json.loads((out/'live-core-report.json').read_text());adapter_sha=sha(out/'source-frame.dll')
assert build['result']=='PASS_PC_SOURCE_FRAME_BUILD' and component['result']=='PASS_PC_SOURCE_FRAME_COMPONENT' and live['result']=='PASS_PC_NORMAL_SOURCE_FRAME_LIVE_CORE'
for report in (build,component,live):
 assert report['adapter_sha256']==adapter_sha
 for name,digest in report['source_sha256'].items():assert sha(source/name)==digest,name
for name,report in [('test_source_frame_component.py',component),('test_source_frame_live.py',live)]:assert sha(source/name)==report['test_sha256']
assert sha(native/'capture-host.dll')==live['core_dll_sha256']
provenance=json.loads((native/'source-provenance.json').read_text())
for name,digest in provenance['unaltered_source_sha256'].items():assert sha(root/('outputs/nfsug-research' if name in ('native_span.c','native_span.h') else 'work')/name)==digest,name
native_build=json.loads((native/'capture-jni-build-report.json').read_text())
for name,digest in native_build['native_inputs'].items():
 if name.endswith(('.c','.h','.inc','CMakeLists.txt','/build_capture.py','/stage_capture.py')):assert sha(root/name)==digest,name
assert component['source_components_equal']==68 and component['missing_components_rejected']==36 and component['malformed_rejected']==9 and component['exact_aggregate_budget_checks']==9
assert live['original_frames']==600 and live['post_reset_original_frames']==80 and live['complete_frames']==590 and live['selected_snapshots']==9 and live['source_components_host_identical']==68 and live['audio_frames']==443007
assert live['capture_never_steps_logic'] and live['wrong_thread_rejected'] and live['reset_disable_rejected'] and live['held_frame_immutable_after_core_close']
exports=subprocess.run(['C:/msys64/mingw64/bin/objdump.exe','-p',str(out/'source-frame.dll')],capture_output=True,text=True,check=True).stdout
for name in ('api_bind_owner','frame_capture','frame_free','frame_info','frame_owner','frame_component'):assert 'nf_pc_source_'+name in exports,name
result=dict(result='PASS_PC_SOURCE_FRAME_INTEGRATION',source_and_test_core_dll_hashes_verified=True,complete_frames=590,selected_snapshots=9,original_frames=600,post_reset_frames=80,original_audio_sha256=live['audio_sha256'],maximum_requested_frame_bytes=live['largest_requested_frame_bytes'],adapter_sha256=adapter_sha,owner_thread_enforced=True,frame_survives_core_close=True,pc_gpu_rendering=False,playable_native_release=False,full_scene_60fps=False)
(out/'integration-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
