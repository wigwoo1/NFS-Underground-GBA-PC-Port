from pathlib import Path
import hashlib,json,subprocess
source=Path(__file__).parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-model-tests';native=base/'NFSUG-android-background-jni-native-local'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((out/'build-report.json').read_text());run=json.loads((out/'model-report.json').read_text());assert build['result']=='PASS_PC_MODEL_BUILD' and run['result']=='PASS_PC_SOURCE_MODEL_MESH'
assert build['dll_sha256']==run['dll_sha256']==sha(out/'source-model.dll') and run['core_sha256']==sha(native/'capture-host.dll')
for report in (build,run):
 for name,digest in report['source_sha256'].items():assert sha(source/name)==digest,name
assert run['test_sha256']==sha(source/'test_model_mesh.py')
for key in ('java_oracle_sources','source_reference_inputs'):
 for name,digest in build[key].items():assert sha(Path(name))==digest,name
assert len(build['source_reference_inputs'])==9 and len(build['reference_sha256'])==193
for name,digest in build['reference_sha256'].items():assert sha(out/'references'/name)==digest
prior=json.loads((base/'NFSUG-pc-source-frame-tests/build-report.json').read_text())
for name in ('source_frame.c','source_frame.h'):assert build['source_sha256'][name]==prior['source_sha256'][name]
inputs=json.loads((native/'capture-jni-build-report.json').read_text())
for name,digest in inputs['native_inputs'].items():
 if name.endswith(('.c','.h','.inc','CMakeLists.txt','/stage_capture.py','/build_capture.py')):assert sha(root/name)==digest,name
assert run['source_frames']==9 and run['reference_models']==29 and run['live_source_models']==29 and run['synthetic_models']==3 and run['model_comparisons']==61 and run['triangle_vertices_compared']==8190 and run['texture_planes_compared']==2730 and run['malformed_rejected']==19
assert run['synthetic_triangle_vertices']=={'synthetic-near':6,'synthetic-back':0,'synthetic-hidden':0} and run['source_frame_release_and_core_close_safe'] and run['mesh_camera_rgba_indices_planes_byte_identical'] and run['source_draw_bounds_order_equal']
exports=subprocess.run(['C:/msys64/mingw64/bin/objdump.exe','-p',str(out/'source-model.dll')],check=True,capture_output=True,text=True).stdout
for name in ('nf_pc_source_model_count','nf_pc_source_model_mesh','nf_pc_model_mesh_decode','nf_pc_model_mesh_info','nf_pc_model_mesh_buffer','nf_pc_model_mesh_plane','nf_pc_model_mesh_free'):assert name in exports
result=dict(result='PASS_PC_SOURCE_MODEL_INTEGRATION',source_oracle_dll_core_hashes_verified=True,source_models=29,synthetic_models=3,model_comparisons=61,triangle_vertices_compared=8190,texture_planes_compared=2730,source_draw_bounds_order_equal=True,malformed_rejected=19,original_prefix_frames=296,clock_hz=16777216,cycles_per_step=280896,model_survives_frame_and_core_close=True,gpu_model_drawing=False,full_scene=False,playable_native_release=False,full_scene_60fps=False,dll_sha256=build['dll_sha256'])
(out/'integration-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
