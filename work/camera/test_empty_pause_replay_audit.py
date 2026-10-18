import json,copy
from pathlib import Path
from verify_pause_replay_commits import verify
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791360500939962400.json').read_text())
a=verify(r);assert sum(x['empty_replay_verified'] for x in a['pauses'])==1
for kind in ('erase_pending','invent_snapshot','advance_submission'):
 altered=copy.deepcopy(r)
 if kind=='erase_pending':altered['pause_events'][0]['buffer_at_begin']['planned_replay_indices']=[]
 elif kind=='invent_snapshot':altered['pause_events'][1]['buffer_at_begin']['snapshot_refreshes']=[9231]
 else:altered['pause_events'][1]['buffer_at_begin']['last_submitted_refresh']+=1
 try:verify(altered)
 except AssertionError:pass
 else:raise AssertionError('Malformed empty replay accepted: '+kind)
print(json.dumps(dict(result='PASS',actual_empty_pause=1,malformed_rejections=3)))
