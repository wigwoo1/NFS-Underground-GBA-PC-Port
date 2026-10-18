"""Summarize measured stages; wall time cannot isolate scheduler or GPU waits."""
import csv, json, sys, statistics
from pathlib import Path
p = Path('work/camera')
rows = list(csv.DictReader((p / sys.argv[1]).open()))
outliers = []
stages = ('renderer_load_ns', 'renderer_draw_ns', 'renderer_hud_ns', 'renderer_finish_ns')
stage_samples = {k: [] for k in stages if k in rows[0]}
for r in rows:
    if not int(r['ready']):
        continue
    sim = (int(r['simulation_end_ns']) - int(r['simulation_start_ns'])) / 1e6
    render = (int(r['render_end_ns']) - int(r['render_start_ns'])) / 1e6
    total = (int(r['render_end_ns']) - int(r['simulation_start_ns'])) / 1e6
    for key in stage_samples:
        value = int(r[key]) / 1e6
        assert 0 <= value <= render, (key, value, render)
        stage_samples[key].append(value)
    if total > 1000 / 60:
        pair = int(r['paired_prepare_ns']) / 1e6
        item = dict(display=int(r['display_index']), refresh=int(r['refresh']),
                             total_ms=total, simulation_ms=sim, render_ms=render,
                             pair_ms=pair, render_excluding_pair_ms=render-pair,
                    dominant='simulation' if sim > render else 'render')
        item.update({k: int(r[k])/1e6 for k in stage_samples})
        outliers.append(item)
report = dict(over_budget=len(outliers),
              simulation_dominant=sum(r['dominant']=='simulation' for r in outliers),
              render_dominant=sum(r['dominant']=='render' for r in outliers),
              renderer_stage_ms={k:dict(median=statistics.median(v),
                                       p95=sorted(v)[int(.95*len(v))], maximum=max(v))
                                 for k,v in stage_samples.items()},
              outliers=outliers,
              scope='Measured host wall-clock stages; no scheduler/GPU wait attribution or scanout proof')
(p / sys.argv[2]).write_text(json.dumps(report, indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='outliers'}))
