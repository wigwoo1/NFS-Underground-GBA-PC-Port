"""Compare completed Android route receipts without equating coverage to playback."""
from pathlib import Path
import hashlib, json

base = Path(r'C:\NFSUG-Workspace')
root = Path(r'Y:\CODEX\NFSUG-Native-PC-Port')
folder = base / 'NFSUG-Android-Context-Refresh-20261017/route-results'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def ranges(steps):
    result = []
    for step in steps:
        if result and step == result[-1][1] + 1:
            result[-1][1] = step
        else:
            result.append([step, step])
    return result

def validate(r):
    n, o = r['native'], r['original']
    assert r['all_original_pixels_audio_clocks_exact']
    assert n['steps'] == o['steps'] == 6000
    assert n['original_frame_hash_chain'] == o['original_frame_hash_chain'] == '8cebc959a53ce0264edee7c5266d32a24cd09b29f9b07b05c4e7fa59cc5eb737'
    assert n['original_audio_frames'] == o['original_audio_frames'] == 4430117
    assert n['original_audio_sha256'] == o['original_audio_sha256'] == 'e3d0620b037591b5e4d2fb1e806448e2635eb056d614dd3710942a3c6b645807'
    missing, failed = n['missing_steps'], n['preparation_failure_steps']
    assert missing == sorted(set(missing)) and failed == sorted(set(failed))
    assert not set(missing) & set(failed)
    assert all(1 <= s <= 6000 for s in missing + failed)
    assert n['captured_preflighted_scenes'] + len(missing) + len(failed) == 6000
    assert not r['gpu_each_scene_verified'] and r['diagnostic_unpaced']
    assert not r['audio_device_used'] and not r['full_scene_60fps']
    return set(missing), set(failed)

old_path = base / 'NFSUG-Android-Native-Wide-20261017/route-results/current-native-route-report.json'
new_path = folder / 'current-native-route-report.json'
old, new = json.loads(old_path.read_text()), json.loads(new_path.read_text())
om, of = validate(old)
nm, nf = validate(new)
assert len(om) == 814 and not of
assert new['runner_sha256'] == sha(root / 'work/android/run_context_refresh_route.py')
assert new['input_keys_sha256'] == old['input_keys_sha256'] == sha(folder / 'input-keys.json')
for variant, key in [('production', 'production_apk_sha256'), ('route-test', 'test_apk_sha256')]:
    p = folder.parent / variant / 'NFSUG-Android-Core-Preview.apk'
    assert new[key] == sha(p)
    receipt = json.loads((p.parent / 'apk-build-report.json').read_text())
    assert receipt['sha256'] == new[key]
report = dict(
    result='VERIFIED_PAIRED_ORIGINAL_PARITY_CONTEXT_REFRESH_COVERAGE_RECORDED',
    original_pixels_pcm_clocks_exact=True,
    steps=6000,
    previous_missing=814,
    current_missing=len(nm),
    recovered_missing_steps=sorted(om - nm - nf),
    newly_missing_steps=sorted(nm - om),
    missing_ranges=ranges(sorted(nm)),
    preparation_failure_steps=sorted(nf),
    cpu_source_coverage_gate_met=not any(s > 10 for s in nm | nf),
    captured_preflighted_scenes=new['native']['captured_preflighted_scenes'],
    strict_model_plane_failures_recovered=new['native']['strict_model_plane_failures_recovered'],
    triangle_planes_checked=new['native']['triangle_planes_checked'],
    full_scene_60fps=False,
    release_allowed=False,
    report_sha256=sha(new_path),
    previous_report_sha256=sha(old_path),
    analyzer_sha256=sha(Path(__file__)),
    scope='Unpaced emulator source capture and CPU preparation. Does not verify GPU output on every step, real-time playback, device audio, physical phone, or full race.'
)
assert report['cpu_source_coverage_gate_met'] == new['cpu_source_coverage_gate_met']
(folder / 'context-refresh-route-analysis.json').write_text(json.dumps(report, indent=2))
print(json.dumps({k: v for k, v in report.items() if k != 'recovered_missing_steps'}, indent=2))
print('Recovered missing scenes:', len(report['recovered_missing_steps']))
