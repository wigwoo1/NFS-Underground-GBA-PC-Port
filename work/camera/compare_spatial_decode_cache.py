"""Alternating fresh source identities, eleven callers per scene pair."""
import time,statistics,json
from pathlib import Path
from types import SimpleNamespace
from owned_spatial_decode_cache_candidate import SpatialDescriptors,_original,cached_init,_local
folder=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/early-pair-8836-20261007/scene-inputs')
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
exec(compile(source,'fixture_setup','exec'));prepared.close();history.close()
payloads=[(s.graph.graph.geometry,s.graph.graph.offsets) for s in scenes];results=[]
for round in range(24):
 row={}
 for mode in (['original','cached'] if round%2==0 else ['cached','original']):
  owners=[SimpleNamespace(geometry=bytes(bytearray(g)),offsets=bytes(bytearray(o))) for i in range(100) for g,o in payloads]
  init=_original if mode=='original' else cached_init
  _local.entries=[];start=time.perf_counter_ns()
  for owner in owners:
   for repeat in range(11):
    value=object.__new__(SpatialDescriptors);init(value,owner)
  row[mode]=(time.perf_counter_ns()-start)/1e6/len(owners)
 results.append(row)
result=dict(result='PASS_ALTERNATING_FRESH_IDENTITY_BENCHMARK',rounds=results,median_original_ms=statistics.median(x['original'] for x in results[4:]),median_cached_ms=statistics.median(x['cached'] for x in results[4:]),scope='Two captured payloads,200fresh identity owners/round,11callers/owner. Byte owner creation outside timer; first4rounds excluded; uncontrolled system load; component not gameplay.')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/spatial-cache-live-20261007/alternating-decode-benchmark.json').write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='rounds'})

