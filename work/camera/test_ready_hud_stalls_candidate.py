import json
from copy import deepcopy
from pathlib import Path
from analyze_ready_hud_stalls_candidate import analyze_ready
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791529991250393800.json').read_text());out=analyze_ready(r)
assert out['total']==43 and out['groups']['ready_transfer']['count']==23 and out['groups']['waited_transfer']['count']==13 and out['groups']['cached_hud']['count']==7
for fault in ('readiness','nested','classification'):
 bad=deepcopy(r);e=next(x for x in bad['bounded_diagnostic_stats']['whole_run_api_intervals']['long_intervals']['records'] if x.get('hud_transfer') and x['hud_transfer']['ready_before_take']);t=e['hud_transfer']
 if fault=='readiness':t['completed_ns']=t['take_begin_ns']+1
 elif fault=='nested':t['take_begin_ns']=e['hud_lease_stages']['snapshot_begin_ns']-1
 else:e['hud_lease_stages']['snapshot_new']=False
 try:analyze_ready(bad)
 except AssertionError:pass
 else:raise AssertionError('Invalid readiness evidence accepted: '+fault)
print('PASS_COMPLETE_READINESS_PARTITION_INVALID_STAMPS_REJECTED')
