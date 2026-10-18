import json
from pathlib import Path
from analyze_consumer_gap_partition import analyze
p=Path('work/camera/prototype-runs');r=json.loads((p/'owned-native-1791426023881163300.json').read_text());load=json.loads((p/'process-cpu-load-1791426009403.json').read_text(encoding='utf-8-sig'));g=analyze(r);rows={x['display_index']:x for x in r['presentation_samples'] if x.get('native_committed_sample')}
for x in g['largest']:
 end=rows[x['display_index']]['native_committed_sample'][6];start=end-round(x['gap_ms']*1e6)
 x['observed_cpu_intervals']=[dict(begin_ns=s['begin_ns'],end_ns=s['end_ns'],top=s['top'][:3]) for s in load['samples'] if s['begin_ns']<end and s['end_ns']>start]
g['scope']+=' One-second process CPU intervals cover part of run; correlation not exclusive cause, no GPU attribution.'
Path('work/camera/async-sky-observed-load-join.json').write_text(json.dumps(g,indent=2));print(json.dumps(g['largest'][:1],indent=2))
