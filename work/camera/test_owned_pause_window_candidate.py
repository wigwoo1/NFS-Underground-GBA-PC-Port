import json
from pathlib import Path
from owned_pause_window_candidate import PauseWindow
v=PauseWindow(2)
for i in range(1000):v.append(dict(begin_ns=i*100,end_ns=i*100+20,duration_ns=20));v[-1]['republished_refreshes']=[i]
assert len(v)==2 and v.total_records==1000 and v.duration_ns==20000 and v.snapshot()[-1]['republished_refreshes']==[999]
try:v.append(dict(begin_ns=0,end_ns=1,duration_ns=1))
except ValueError:pass
else:raise AssertionError('Overlapping history accepted')
assert v.total_records==1000
out=dict(result='PASS_PAUSE_WINDOW',stats=v.stats(),scope='1000 completed intervals, mutable latest metadata, invalid interval rejection. Live verification pending.')
Path('work/camera/prototype-runs/native-pause-window-tests.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
