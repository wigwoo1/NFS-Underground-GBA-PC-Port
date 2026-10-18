import json
from pathlib import Path
p=Path('work/camera');r=json.loads((p/'prototype-runs/owned-native-1791425748214806700.json').read_text());c=json.loads((p/'prototype-runs/async-sky-crops-1791425751453536900.json').read_text());g=json.loads((p/'async-crop-minute-gap-partition.json').read_text())
completed=c['reports'][0]['completed'];last=max(x['display_index'] for x in completed);first=min(x['display_index'] for x in completed)
during=[x for x in g['largest'] if first<=x['display_index']<=last];after=[x for x in g['largest'] if x['display_index']>last]
totals={}
for gap in g['largest']:
 for part in gap['parts']:totals[part['stage']]=totals.get(part['stage'],0)+part['ms']
result=dict(result='PASS_CAPTURE_WINDOW_STALL_JOIN',capture_first=first,capture_last=last,stalls_during_capture=len(during),stalls_after_capture=len(after),stalls_before_capture=len(g['largest'])-len(during)-len(after),stall_partition_total_ms=totals,largest_gap=g['largest'][0],scope='Capture submissions stop after bounded120attempt window. Empty polls remain. Later stalls cannot be assigned to active crop readback alone; timestamps do not isolate producer work from OS scheduling, preparation contention or competing CPU load.')
(p/'async-crop-minute-stall-window.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='largest_gap'},indent=2))
