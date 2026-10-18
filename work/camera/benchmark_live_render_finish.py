"""Alternating live finish modes; retain every run and compare shared input prefixes."""
from pathlib import Path
import csv, hashlib, json, os, subprocess, sys, time

p = Path(__file__).resolve().parent
stamp = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
priority = '--priority' in sys.argv
archive = p / 'prototype-runs' / (('priority-comparison-' if priority else 'finish-comparison-') + stamp)
archive.mkdir()
runs = []
for index, asynchronous in enumerate((False, True, False, True)):
    env = {k: v for k, v in os.environ.items() if not k.startswith('NF_')}
    env.update(NF_TEST_RACING_SECONDS='12', NF_TEST_RACING_STEERING='1',
               NF_TEST_DIRECT_CAPTURE_RAM='1', NF_TEST_DIRECT_CAPTURE_ROM='1',
               NF_LAYER_DIRTY='1', NF_TEST_DISTINCT_OCCURRENCE_GEOMETRY='1',
               NF_TEST_CLOCK_BACKLOG_PROFILE='1', NF_TEST_THREAD_CPU_PROFILE='1')
    if asynchronous:
        env['NF_TEST_ABOVE_NORMAL_THREADS' if priority else 'NF_TEST_ASYNC_RENDER_FINISH'] = '1'
    label = str(index) + (('-above-normal' if asynchronous else '-normal') if priority else ('-async' if asynchronous else '-sync'))
    started = time.time_ns()
    result = subprocess.run([sys.executable, str(p / 'audit_threaded_racing_motion.py')],
                            env=env, capture_output=True, text=True, timeout=75)
    (archive / (label + '.log')).write_text(result.stdout + result.stderr)
    report = json.loads((p / 'threaded-racing-motion-audit.json').read_text())
    # A stale report must never certify a failed or interrupted new process.
    assert (p / 'threaded-racing-motion-audit.json').stat().st_mtime_ns >= started
    assert json.dumps(report['prefix']) in result.stdout, result.stderr
    retained = {'mode': label, 'exit_code': result.returncode, 'live': report}
    if priority and asynchronous:
        assert report['host_stats']['producer_priority_after'] == 1
        assert report['host_stats']['worker_priority_after'] == 1
    for script, filename, key in (
        ('audit_presentation_pacing.py', 'presentation-pacing-audit.json', 'pacing'),
        ('audit_thread_cpu_components.py', 'thread-cpu-component-audit.json', 'cpu')):
        check = subprocess.run([sys.executable, str(p / script)], capture_output=True,
                               text=True, timeout=20)
        (archive / (label + '-' + key + '.log')).write_text(check.stdout + check.stderr)
        if check.returncode == 0:
            retained[key] = json.loads((p / filename).read_text())
        else:
            retained[key] = {'failed': True, 'exit_code': check.returncode}
    inputs = list(csv.DictReader(Path(report['prefix'] + '-input.csv').open()))
    retained['keys'] = [int(row['keys']) for row in inputs]
    retained['input_sha256'] = hashlib.sha256(json.dumps(retained['keys']).encode()).hexdigest()
    runs.append(retained)
    (archive / 'runs.json').write_text(json.dumps(runs, indent=2))
    print(label, result.returncode, report['original_updates'], retained['pacing'], flush=True)

shared = min(len(run['keys']) for run in runs)
assert all(run['keys'][:shared] == runs[0]['keys'][:shared] for run in runs)
output = dict(runs=runs, priority_comparison=priority, shared_original_input_prefix=shared,
              all_required_live_gates_passed=all(run['exit_code'] == 0 for run in runs),
              scope='No readbacks. Each live RAM image checked against its exact original input replay; shared input prefix compared across modes. Wall-clock runs can finish at different original updates. Logged commit timing is not scanout or GPU completion. No 60fps proof.')
(archive / 'comparison.json').write_text(json.dumps(output, indent=2))
print('retained', archive, 'shared_prefix', shared, flush=True)
