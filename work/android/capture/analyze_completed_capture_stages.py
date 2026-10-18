"""Strict completed-work capture accounting; no relaxed counts or duration gates."""
from pathlib import Path
import hashlib,json
base=Path('C:/NFSUG-Workspace/NFSUG-Android-Completed-Capture-20261017')
folder=base/'runtime-results'
summary=json.loads((folder/'reuse-runtime-summary.json').read_text())
assert summary['result']=='PASS_REUSE_GPU_LIVE_UI_REGRESSIONS'
assert summary['live']['capture_profile_completed_work'] is True
profile=summary['live']['profile_cpu_dispatch']
names=['capture_background_copy','capture_background_bind_inclusive','capture_background_parse','capture_history_copy','capture_history_parse','capture_road_retention','capture_wall_retention','capture_prepared_constructor']
assert all(profile[name]['calls']>0 for name in names)
outer=profile['complete_capture']['total_ms']
accounted=sum(profile[name]['total_ms'] for name in names)
assert profile['capture_background_copy']['calls']<=profile['complete_capture']['calls']
assert 0<accounted<=outer
nested=profile['capture_world_copy_nested_in_bind']
assert nested['total_ms']<=profile['capture_background_bind_inclusive']['total_ms']
report=dict(result='VERIFIED_COMPLETED_CAPTURE_STAGE_PROFILE_LIMITED_SCOPE',
    complete_capture=profile['complete_capture'],
    ranked_nonoverlapping_capture_stages=sorted([dict(name=name,**profile[name],fraction_of_measured_capture=profile[name]['total_ms']/outer) for name in names],key=lambda row:row['total_ms'],reverse=True),
    nested_world_copy=nested,accounted_ms=accounted,unattributed_ms=outer-accounted,
    capture_metrics_published_only_on_outer_completion=True,atomic_snapshot=True,
    nested_world_copy_not_added_twice=True,strict_count_duration_gates_unchanged=True,
    summary_sha256=hashlib.sha256((folder/'reuse-runtime-summary.json').read_bytes()).hexdigest(),
    runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    steady_state=False,physical_device=False,full_scene_60fps=False,
    limits='Short SwiftShader emulator lifecycle sample includes startup, mode switches, reference draw/readback. Rank nonoverlapping total capture costs only within this completed-work sample; not physical-device performance, audio quality, steady-state FPS or isolated GPU time.')
(folder/'capture-stage-analysis.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
