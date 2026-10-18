"""Correlate every retained finish-comparison run, including single-commit failures."""
from pathlib import Path
import csv, json, sys

p = Path(__file__).resolve().parent
archive = Path(sys.argv[1]) if len(sys.argv) > 1 else max(
    p.joinpath('prototype-runs').glob('finish-comparison-*'), key=lambda x: x.stat().st_mtime_ns)
runs = json.loads((archive / 'runs.json').read_text())
checks = []
for run in runs:
    prefix = run['live']['prefix']
    def rows(kind):
        return list(csv.DictReader(Path(prefix + '-' + kind + '.csv').open()))
    worker, inputs, producer = rows('worker'), rows('input'), rows('producer')
    assert inputs and worker
    commits = [x for x in worker if int(x['committed']) == 1 and int(x['result']) == 0]
    lo, hi = int(inputs[0]['start_ns']), int(inputs[-1]['end_ns'])
    edges = [lo] + [int(x['commit_begin_ns']) for x in commits if lo < int(x['commit_begin_ns']) < hi] + [hi]
    gap_lo, gap_hi = max(zip(edges, edges[1:]), key=lambda x: x[1] - x[0])
    busy = sum(max(0, min(gap_hi, int(x['end_ns'])) - max(gap_lo, int(x['start_ns']))) for x in inputs)
    original_cpu = [x for x in rows('producer-cpu') if x['kind'] == 'original_tick']
    overlapping = [x for x in original_cpu if int(x['begin_ns']) < gap_hi and int(x['end_ns']) > gap_lo]
    cpu = sum(int(x['cpu_end_ns']) - int(x['cpu_begin_ns']) for x in overlapping)
    origin, base = int(worker[0]['clock_origin']), int(worker[0]['source_base'])
    debt = [max(0, (int(x['end_ns']) - origin) * 16777216 // (1000000000 * 280896)
                - (int(x['after']) - base)) for x in inputs]
    pushes = [x for x in producer if gap_lo <= int(x['begin_ns']) < gap_hi and int(x['pushed'])]
    checks.append(dict(mode=run['mode'], live_result=run['live']['result'], commits=len(commits),
                       longest_window_without_commit_ms=(gap_hi-gap_lo)/1e6,
                       gap_original_tick_wall_ms=busy/1e6,
                       overlapping_tick_cpu_ms=cpu/1e6, overlapping_tick_count=len(overlapping),
                       successful_pushes_during_gap=len(pushes), max_original_backlog=max(debt),
                       ticks_ending_behind=sum(x > 0 for x in debt), original_updates=len(inputs)))
out = dict(result='RETAINED_STARVATION_CORRELATION', checks=checks,
           scope='Includes startup and shutdown windows, unlike interior-only pacing audit. CPU sums include full overlapping ticks; wall sums clipped to gap. Backlog uses original GBA timing. Correlation does not prove OS scheduling or GPU causality.')
(archive / 'starvation.json').write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
