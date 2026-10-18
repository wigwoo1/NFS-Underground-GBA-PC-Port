import json,statistics
from pathlib import Path
root=Path('G:/EXTRA DATA DRIVE/Desktop/Games/Codex/NFSUG-Native-PC-Port/work/camera')
candidate=json.loads((root/'prototype-runs/existing-model-index-clock-cleanup-20261010.json').read_text())
baseline=json.loads(Path('prepared_hud_live_audit.json').read_text())
def summarize(a,expected):
    r=json.loads(Path(a['source']).read_text())
    requests=[s for s in r['world_preparation_stage_samples'] if s['terminal'][-1]['fine_trace']]
    assert requests and all(s['terminal'][-1]['model_visit_callable']['module']==expected for s in requests)
    values={}
    for s in requests:
        for sample in s['terminal'][-1]['sample_timings']:
            for stage in sample['source_sample_stages']:
                values.setdefault(stage['name'],[]).append(stage['wall_ns']/1e6)
    return dict(source=a['source'],cadence=a['coverage']['active_intervals'],selected_module=expected,
                stages={name:dict(count=len(v),median_ms=statistics.median(v),max_ms=max(v)) for name,v in values.items()})
out=dict(candidate=summarize(candidate,'owned_model_visit_index_install_candidate'),baseline=summarize(baseline,'owned_sampled_model_visit'),scope='One candidate then baseline order with matching bounded fine trace; different runtime scheduling remains. No causal or sustained60 proof.')
Path('model_index_followup_comparison.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))
