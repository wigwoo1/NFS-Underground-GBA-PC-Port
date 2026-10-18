from pathlib import Path
import json,hashlib,subprocess,sys
source=Path(__file__).resolve().parent;out=Path(r"C:\NFSUG-Workspace\NFSUG-pc-model-tests")
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((out/'model-gpu-build-report.json').read_text())
for name,digest in build['source_sha256'].items():assert sha(source/name)==digest,('Changed production/test input',name)
for path,digest in build['reference_sha256'].items():assert sha(Path(path))==digest,('Changed reference',path)
assert sha(out/'model-gpu.dll')==build['dll_sha256']
for test in ['test_model_cross_gpu.py','test_model_nearest_boundary.py']:subprocess.run([sys.executable,str(source/test)],check=True)
r=json.loads((out/'model-cross-gpu-report.json').read_text());old=json.loads((out/'model-gpu-report.json').read_text());near=json.loads((out/'model-nearest-boundary-report.json').read_text())
assert r['models']==32 and r['targets']==37 and r['pixel_comparisons']==26188800
assert r['native_dll_sha256']==build['dll_sha256'] and r['reference_shader_unchanged']
for a,b in zip(r['frames'],old['frames']):
 assert (a['model'],a['width'],a['height'],a['top'],a['bottom'])==(b['model'],b['width'],b['height'],b['owner_top'],b['owner_bottom'])
 assert a['native_sha256']==b['sha256'],'Native output changed between reference comparisons'
assert len(near['cases'])==11 and all(c['full_rectangle_exact'] for c in near['cases'])
for name,digest in r['test_source_sha256'].items():assert sha(source/name)==digest
assert sha(source/'test_model_nearest_boundary.py')==near['test_sha256']
report=dict(result='PASS_PC_MODEL_INDEPENDENT_GLES_DIAGNOSTIC_INTEGRATION',production_renderer_unchanged=True,native_outputs_identical_to_prior_37_cases=True,independent_gles_shader_unchanged=True,exact_nearest_boundary_cases=11,model_pixel_comparisons=r['pixel_comparisons'],cross_gpu_pixel_differences=r['mismatched_pixels'],coverage_max_edge_distance_pixels=r['coverage_max_edge_distance_pixels'],color_max_texel_boundary_distance_outside_edge=r['color_max_texel_boundary_distance_outside_edge'],model_fidelity_exact=False,full_scene=False,playable_native_release=False,full_scene_60fps=False,source_sha256={n:sha(source/n) for n in ['gles_model_reference.py','test_model_cross_gpu.py','test_model_nearest_boundary.py','verify_model_cross_gpu.py']},reports_sha256={n:sha(out/n) for n in ['model-cross-gpu-report.json','model-nearest-boundary-report.json','model-gpu-build-report.json']})
(out/'model-cross-gpu-integration-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
