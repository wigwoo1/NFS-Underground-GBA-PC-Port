import json,time,statistics
from pathlib import Path
from types import SimpleNamespace
from owned_ordinary_model_visits import owned_object_chains as original
from owned_object_chain_views_candidate import owned_object_chains as candidate
folder=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/exact-pair-10331-20261007/scene-inputs');payloads=[(folder/(n+'.objects.bin')).read_bytes() for n in ('older','newer')];rows=[]
for round in range(24):
 row={}
 for name,fn in ([('original',original),('candidate',candidate)] if round%2==0 else [('candidate',candidate),('original',original)]):
  owners=[SimpleNamespace(objects=payloads[i%2]) for i in range(200)];start=time.perf_counter_ns()
  for owner in owners:fn(owner)
  row[name]=(time.perf_counter_ns()-start)/1e6/len(owners)
 rows.append(row)
out=dict(result='PASS_COLD_OWNER_BENCHMARK',rounds=rows,median_original_ms=statistics.median(x['original'] for x in rows[4:]),median_candidate_ms=statistics.median(x['candidate'] for x in rows[4:]),scope='Alternating200 fresh owner identities each round, same two immutable payloads, first4warmupexcluded; owner creation outside timing. Uncontrolled system load; not fullscene benefit or physical cadence proof.')
Path('work/camera/object-chain-views-performance.json').write_text(json.dumps(out,indent=2));print(out)
