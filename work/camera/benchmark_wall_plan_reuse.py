"""Full fixed route: retained saved-input recomputation versus exact plan reuse."""
from pathlib import Path
import json, os, subprocess, sys, time

p = Path(__file__).resolve().parent
surface_read = '--surface-read' in sys.argv
archive = p / 'prototype-runs' / (('surface-read-comparison-' if surface_read else 'wall-plan-comparison-') + time.strftime('%Y%m%dT%H%M%SZ', time.gmtime()))
archive.mkdir()
env = {k:v for k,v in os.environ.items() if not k.startswith(('NF_', 'BENCH_'))}
env.update(BENCH_UPDATES='720', BENCH_LIVE_ROUTE='1', BENCH_NF_TEST_DIRECT_CAPTURE_ROM='1')

def run(label, mode, current):
    result = subprocess.run([sys.executable, str(p / 'benchmark_race_capture.py'), mode],
                            env=current, capture_output=True, text=True, timeout=90)
    (archive / (label + '.log')).write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout.split('BENCHMARK_JSON=')[-1])
    (archive / (label + '.json')).write_text(json.dumps(report, indent=2))
    return report

baseline = run('baseline', 'baseline', env)
env['BENCH_BASELINE_JSON'] = json.dumps(baseline)
runs = []
for index, verify in enumerate((False, True, False, True)):
    current = dict(env)
    if verify:
        current['BENCH_NF_TEST_SURFACE_READ_REUSE' if surface_read else 'BENCH_NF_VERIFY_WALL_PLAN_REUSE'] = '1'
    label = str(index) + (('-reuse' if verify else '-original') if surface_read else ('-recompute-verify' if verify else '-reuse'))
    report = run(label, 'direct-dirty-profile', current)
    assert report['ram_sha256'] == baseline['ram_sha256']
    if runs:
        assert report['completion_ledger'] == runs[0]['report']['completion_ledger']
    event = next(x for x in report['events'] if int(x['pc'], 16) == 0x0300264c)
    runs.append(dict(mode=label, wall_plan_event=event, report=report))
    (archive / 'runs.json').write_text(json.dumps(runs, indent=2))
    print(label, 'CPU', report['cpu_ms'], 'wall', report['wall_ms'], 'wall_plan', event, flush=True)
output = dict(result='PASS_FULL_ROUTE_STATE_COMPONENT', surface_read_comparison=surface_read, baseline=baseline, runs=runs,
              scope='720 identical original input updates, scene completion ledger and final original RAM. Surface-read mode alternates original/reused reads without reference recomputation. Wall-plan recompute mode also strictly compares saved-input output and adds comparison overhead. Profiled component costs exclude GPU and live scheduling; no 60fps or causal whole-game speedup proof.')
(archive / 'comparison.json').write_text(json.dumps(output, indent=2))
print('retained', archive, flush=True)
