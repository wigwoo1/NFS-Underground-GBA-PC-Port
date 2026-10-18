"""Validate exercised texture hint reuse and summarize full-route evidence."""
from pathlib import Path
import json,re,hashlib
p=Path('work/camera');report=json.loads((p/'road-attribute-live-layer-sync-tests.json').read_text())
replay=json.loads((p/'traffic-texture-hints-hud-replay-tests.json').read_text())
assert report['result']=='PASS' and report['duration_seconds']==60
assert replay['result']=='PASS' and replay['exact_live_frames']==12
log=report['host_output']
values={key:int(re.search(r'\b'+key+r'=(\d+)',log)[1]) for key in ('texture_uploads','texture_hits','texture_evictions','texture_uploaded_bytes','texture_hint_hits','texture_hash_bytes_saved')}
assert 0<values['texture_hint_hits']<=values['texture_hits'] and values['texture_hash_bytes_saved']>0
baseline=json.loads(Path('outputs/nfsug-native-renderer/camera-research/traffic-live-60s-tests.json').read_text())
assert baseline['ram_hashes']==report['ram_hashes']
summary=dict(result='PASS',counters=values,refreshes=report['refreshes'],ram_hashes=report['ram_hashes'],
             exact_4K_replay_frames=replay['exact_live_frames'],
             current_swap_interval_ms=report['swap_interval_ms'],historical_swap_interval_ms=baseline['swap_interval_ms'],
             source_sha256=hashlib.sha256((p/'preview_resources.h').read_bytes()).hexdigest(),
             scope='Exact owned-byte comparisons exercised the hint path, skipping repeated content-hash input processing; original full-route RAM preserved and twelve native4K frames unchanged. Still compares full bytes for reuse. Historical timing is uncontrolled, not causal gain or smooth60fps/scanout proof.')
(p/'texture-hint-live-tests.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
