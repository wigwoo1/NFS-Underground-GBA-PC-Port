import json,statistics
from pathlib import Path
root=Path('G:/EXTRA DATA DRIVE/Desktop/Games/Codex/NFSUG-Native-PC-Port/work/camera')
base=json.loads((root/'prototype-runs/model-index-base60-selection-20261010.json').read_text())
candidate=json.loads(Path('model_index_long_1_audit.json').read_text())
def metrics(a):
    r=json.loads(Path(a['source']).read_text())
    rows=[s for s in r['world_preparation_stage_samples'] if not s['history_only']]
    out={}
    for name,values in [('service_ms',[(s['completed_ns']-s['started_ns'])/1e6 for s in rows]),('queue_ms',[s['queue_wait_ns']/1e6 for s in rows])]:
        values.sort();out[name]=dict(count=len(values),median=statistics.median(values),p95=values[int(.95*(len(values)-1))],maximum=values[-1])
    return dict(cadence=a['cadence'],selected_module=a['selected_module'],requests=out)
out=dict(baseline=metrics(base),candidate=metrics(candidate),scope='Sequential original/index60s pair; fine and gap traces disabled, other diagnostics retained. Source schedules may differ; no causal or physical smooth60 proof.')
Path('model_index_long_comparison.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
