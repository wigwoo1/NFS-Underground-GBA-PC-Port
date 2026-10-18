import json,sys
from pathlib import Path
a=json.loads(Path('prepared_hud_live_audit.json').read_text());r=json.loads(Path(a['source']).read_text())
expected='owned_model_visit_index_install_candidate' if sys.argv[1]=='1' else 'owned_sampled_model_visit'
requests=r['world_preparation_stage_samples'];assert requests
assert all(not s['terminal'][-1]['fine_trace'] for s in requests)
assert all(s['terminal'][-1]['model_visit_callable']['module']==expected for s in requests)
stats=r['bounded_diagnostic_stats']['whole_run_api_intervals']
assert 'compact_gap_diagnostic' not in stats and 'deadline_diagnostic' not in stats
assert a['updates']>3400
out=dict(result='PASS_LONG_ORIGINAL_CLOCK_SELECTION_AND_CLEANUP',source=a['source'],selected_module=expected,
         requests=len(requests),updates=a['updates'],cadence=a['coverage']['active_intervals'],
         scope='60-second fullscene original-clock run; detailed fine/gap observers disabled, aggregate and other caller profiles remain. Cadence and physical scanout qualification separate.')
Path('model_index_long_'+sys.argv[1]+'_audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
