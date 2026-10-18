"""Check long-run scheduling without pretending the short reference covers it."""
import csv, json, re, statistics, sys
from collections import Counter
from pathlib import Path

prefix = Path(sys.argv[1])
seconds = int(sys.argv[2])
rows = list(csv.DictReader(Path(str(prefix) + '-timing.csv').open()))
log = Path(str(prefix) + '-log.txt').read_text()
assert 'result=0 ' in log
base = int(rows[0]['refresh']) - int(rows[0]['simulated'])
previous = -1
missing_run = longest_missing = skipped = rendered = 0
for row in rows:
    tick, poll, sim = (int(row[k]) for k in ('display_index', 'poll_ns', 'simulated'))
    assert tick == poll * 60 // 10**9
    assert sim == poll * 16777216 // (10**9 * 280896)
    assert int(row['refresh']) == base + sim
    assert int(row['deadline_ns']) == (tick * 10**9 + 59) // 60
    assert int(row['skipped']) == tick - previous - 1
    assert abs(float(row['target']) - (base + tick * 16777216 / (280896 * 60) - 5)) < 1e-8
    ready = int(row['ready'])
    assert ready in (0, 1)
    if ready:
        assert 0 <= float(row['alpha']) <= 1
        assert int(row['older']) <= int(row['newer'])
        missing_run = 0
    else:
        assert int(row['older']) == int(row['newer']) == 0
        missing_run += 1
        longest_missing = max(longest_missing, missing_run)
    rendered += ready
    skipped += int(row['skipped'])
    previous = tick
assert previous == seconds * 60 - 1
assert len(rows) + skipped == seconds * 60
assert int(re.search(r'swaps=(\d+)', log)[1]) == len(rows)
late = [(int(r['swap_end_ns']) - int(r['deadline_ns'])) / 1e6 for r in rows if int(r['display_index']) >= 30]
report = dict(result='PASS', seconds=seconds, swaps=len(rows), rendered=rendered,
              unavailable=len(rows)-rendered, longest_unavailable_run=longest_missing,
              skipped=skipped, warm_max_swap_lateness_ms=max(late),
              warm_mean_swap_lateness_ms=statistics.mean(late),
              scope='Hidden-window scheduling/count checks only. Longer-run scene correctness, visible scanout and input latency are not established.')
if 'timeline_status' in rows[0]:
    unavailable = [r for r in rows if r['ready']=='0']
    status_names = {0:'empty', 1:'before_history', 2:'ready_but_rejected', 3:'after_latest_scene'}
    report['unavailable_causes'] = dict(Counter(status_names[int(r['timeline_status'])] for r in unavailable))
    report['epoch_mismatches'] = sum(int(r['epoch_mismatch']) for r in rows)
    for r in rows:
        if r['timeline_status']=='3':
            assert float(r['target']) > int(r['latest_scene_end'])
    after = [float(r['target'])-int(r['latest_scene_end']) for r in rows if r['timeline_status']=='3']
    report['max_target_ahead_of_latest_scene_refreshes'] = max(after,default=0)
    report['lighting_fallback_causes'] = {k:int(rows[-1]['lighting_'+k]) for k in ('range','narrow','sample')}
if 'repeated' in rows[0]:
    last_render_target = None
    for r in rows:
        target = float(r['target'])
        repeat = int(r['repeated'])
        expected_repeat = (r['ready']=='0' and r['timeline_status']=='3' and
                           r['epoch_mismatch']=='0' and last_render_target is not None and
                           0 <= target-last_render_target <= 2)
        assert repeat == int(expected_repeat)
        if r['ready']=='1':last_render_target=target
        elif not repeat:last_render_target=None
    report['repeated_frames'] = sum(int(r['repeated']) for r in rows)
    report['blank_frames'] = len(rows)-rendered-report['repeated_frames']
    report['hold_scope'] = 'Exact prior framebuffer repeated for at most two original refreshes. Repeats are not fresh motion samples.'
Path(str(prefix) + '-tests.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
