import json,collections
from pathlib import Path
cp=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/graphics-only-owned-game-20261008')
rows=json.loads((cp/'token-linked-events.json').read_text())
starts=[r for r in rows if r['pid']==43788 and r['event_id']==215]
def key(r):return (r['fields'].get('hAdapter'),r['fields'].get('Token'))
keys=collections.Counter(key(r) for r in starts)
exact=[r for r in rows if key(r) in keys]
other=[r for r in rows if key(r) not in keys]
result={'result':'AMBIGUOUS_KEYS_NO_DISPLAY_CERTIFICATION','owned_starts':len(starts),'unique_adapter_token_keys':len(keys),'reused_owned_keys':sum(v>1 for v in keys.values()),'same_key_records':len(exact),'rejected_other_adapter_records':len(other),'same_key_groups':[{'pid':k[0],'event_id':k[1],'count':v} for k,v in collections.Counter((r['pid'],r['event_id']) for r in exact).items()],'scope':'Same adapter/token values narrow candidates but recycled keys cannot uniquely identify204frame lifecycles. No nearest-time assignment or completion/cadence output.'}
assert result['reused_owned_keys']>0
(cp/'token-ambiguity.json').write_text(json.dumps(result,indent=2))
(cp/'same-adapter-token-events.json').write_text(json.dumps(exact,indent=2))
print(json.dumps(result,indent=2))
