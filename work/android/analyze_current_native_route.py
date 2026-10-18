"""Assess recorded Android route parity separately from native-scene coverage."""
from pathlib import Path
import hashlib,json
source=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-Android-Native-Current-20261017/route-results';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((out/'current-native-route-report.json').read_text());n=r['native'];o=r['original'];assert r['all_original_pixels_audio_clocks_exact'] and n['steps']==o['steps']==6000
assert n['original_frame_hash_chain']==o['original_frame_hash_chain']=='8cebc959a53ce0264edee7c5266d32a24cd09b29f9b07b05c4e7fa59cc5eb737'
assert n['original_audio_frames']==o['original_audio_frames']==4430117 and n['original_audio_sha256']==o['original_audio_sha256']=='e3d0620b037591b5e4d2fb1e806448e2635eb056d614dd3710942a3c6b645807'
assert r['runner_sha256']==sha(source/'run_current_native_route.py')
missing=n['missing_steps'];failed=n['preparation_failure_steps'];assert sorted(set(missing))==missing and not failed and len(missing)+n['captured_preflighted_scenes']==6000
ranges=[]
for step in missing:
 if ranges and step==ranges[-1][1]+1:ranges[-1][1]=step
 else:ranges.append([step,step])
pc=json.loads((base/'NFSUG-pc-traffic-refresh2-route-tests/diverse-route-report.json').read_text());pc_missing=[x['step'] for x in pc['failures']];assert pc_missing==list(range(1,11))
additional=sorted(set(missing)-set(pc_missing));assert len(missing)==836 and len(additional)==826 and n['captured_preflighted_scenes']==5164 and n['strict_model_plane_failures_recovered']==0
report=dict(result='VERIFIED_ANDROID_ORIGINAL_PARITY_NATIVE_COVERAGE_GATE_FAILED',steps=6000,captured_preflighted_scenes=5164,missing_source_scenes=836,additional_to_verified_pc_route=826,missing_ranges=ranges,longest_missing_run=max(b-a+1 for a,b in ranges),first_post_startup_gap=additional[0],preparation_failures=0,triangle_planes_checked=n['triangle_planes_checked'],runtime_strict_model_planes_recovered=0,frozen_model_plane_failure_steps_unavailable=[s for s in [3593,3800] if s in missing],original_pixels_pcm_clocks_exact=True,native_source_coverage_gate_met=False,full_scene_60fps=False,physical_device_verified=False,route_report_sha256=sha(out/'current-native-route-report.json'),script_sha256=sha(Path(__file__)),next_dependency='Localize why the first post-startup retained scene at82 is null: original background, source-world callback, road, wall or ownership proof; then inspect exact producer context instead of guessing capacity changes.',limits='Unpaced CPU capture/preflight, no GPU draw every scene or AudioTrack playback; elapsed times are diagnostic overhead, not gameplay frame-rate measurements.')
(out/'native-route-analysis.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
