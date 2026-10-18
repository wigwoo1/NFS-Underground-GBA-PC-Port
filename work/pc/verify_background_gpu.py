from pathlib import Path
import hashlib,json,subprocess
source=Path(__file__).parent;root=source.parent.parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-background-tests';native=base/'NFSUG-android-background-jni-native-local'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((out/'build-report.json').read_text());run=json.loads((out/'background-gpu-report.json').read_text());assert build['result']=='PASS_PC_BACKGROUND_BUILD' and run['result']=='PASS_PC_SOURCE_BACKGROUND_GPU'
assert build['dll_sha256']==run['adapter_sha256']==sha(out/'source-background.dll') and run['core_sha256']==sha(native/'capture-host.dll')
for report in (build,run):
 for name,digest in report['source_sha256'].items():assert sha(source/name)==digest,name
assert run['test_sha256']==sha(source/'test_background_gpu_live.py')
for key in ('java_oracle_sources','source_reference_inputs'):
 for name,digest in build[key].items():assert sha(Path(name))==digest,name
assert len(build['source_reference_inputs'])==9 and len(build['reference_sha256'])==27
for name,digest in build['reference_sha256'].items():assert sha(out/'references'/name)==digest
prior=json.loads((base/'NFSUG-pc-source-frame-tests/integration-report.json').read_text());assert prior['result']=='PASS_PC_SOURCE_FRAME_INTEGRATION'
prior_build=json.loads((base/'NFSUG-pc-source-frame-tests/build-report.json').read_text())
for name in ('source_frame.c','source_frame.h'):assert build['source_sha256'][name]==prior_build['source_sha256'][name]
inputs=json.loads((native/'capture-jni-build-report.json').read_text())
for name,digest in inputs['native_inputs'].items():
 if name.endswith(('.c','.h','.inc','CMakeLists.txt','/stage_capture.py','/build_capture.py')):assert sha(root/name)==digest,name
assert run['source_frames']==9 and run['source_background_cells']==345600 and run['historical_palette_entries']==368640 and run['source_sky_cells']==345600 and run['native_gpu_frames']==9 and run['four_k_frames']==3
assert run['native_gpu_pixel_comparisons']==384000 and run['four_k_pixel_comparisons']==24883200 and run['original_prefix_frames']==296 and run['short_output_and_thread_guards'] and run['context_recreated_on_render_thread_after_core_close']
assert not run['full_scene'] and not run['full_scene_60fps']
exports=subprocess.run(['C:/msys64/mingw64/bin/objdump.exe','-p',str(out/'source-background.dll')],check=True,capture_output=True,text=True).stdout
for name in ('nf_pc_source_background_rgba','nf_pc_source_palette_rgba','nf_pc_source_sky_rgba','nf_pc_background_gpu_open','nf_pc_background_gpu_draw','nf_pc_background_gpu_close'):assert name in exports
result=dict(result='PASS_PC_BACKGROUND_GPU_INTEGRATION',source_oracle_dll_core_hashes_verified=True,source_frames=9,four_k_frames=3,gpu_pixels_compared=25267200,renderer=run['renderer'],context_recreated_after_core_close=True,original_prefix_frames=296,clock_hz=16777216,cycles_per_step=280896,component_only=True,full_scene=False,playable_native_release=False,full_scene_60fps=False,dll_sha256=build['dll_sha256'],initial_background_png_sha256=sha(out/'initial-source-background-4k.png'))
(out/'integration-report.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
