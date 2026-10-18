"""Separate whole-run sky phase coverage from visible display qualification."""
import json, sys
from pathlib import Path
r=json.loads(Path(sys.argv[1]).read_text())
s=r['bounded_diagnostic_stats']['whole_run_sky_motion']
a=r['bounded_diagnostic_stats']['whole_run_api_intervals']
assert r['sky_continuous_enabled'] and r['sky_interpolation_enabled'] and r['sky_capture_enabled']
assert s['adjacent_transitions']==a['adjacent_successful_intervals']
assert s['excluded_identity_discontinuities']==a['excluded_discontinuities']
assert 0<=s['stationary_with_unchanged_source_angles']<=s['stationary_transitions']<=s['adjacent_transitions']
assert s['api_intervals_over_25ms']==a['over_25ms']
unexpected=s['stationary_transitions']-s['stationary_with_unchanged_source_angles']
out=dict(result='PASS_WHOLE_SKY_PHASE_COVERAGE' if unexpected==0 else 'FAIL_UNEXPLAINED_SKY_PHASE_HOLDS', transitions=s['adjacent_transitions'], moving_transitions=s['adjacent_transitions']-s['stationary_transitions'], legitimate_source_holds=s['stationary_with_unchanged_source_angles'], unexplained_phase_holds=unexpected, intervals_over_25ms=a['over_25ms'],native_commit_intervals_over_25ms=s['commit_intervals_over_25ms'], intervals_over_33ms=a['over_33_333ms'], max_api_interval_ms=a['max_ms'], visible_60fps_verified=False, scope='Recorded source phase counters and API timing only; no independent GPU pixel or scanout proof. Passing coverage does not qualify smooth 60fps.')
Path(sys.argv[2]).write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
if unexpected:sys.exit(1)
