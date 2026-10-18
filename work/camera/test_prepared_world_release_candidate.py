import json,ctypes as C,hashlib,weakref
from pathlib import Path
from owned_road_record_diagnostic import decode
from owned_road_history_diagnostic import restore
from owned_sample_signature import signature
report=json.loads(Path('work/camera/prototype-runs/owned-native-1791434872973979000.json').read_text())
folder=Path(report['live_preparation_profiles'][0]['capture'])
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
exec(compile(source,'captured_scene_setup','exec'));prepared.close();history.close()
from owned_prepared_world_release_candidate import PreparedWorldMotion as Candidate
from owned_precomputed_source_cached_library_candidate import PrecomputedSourceWorldSamples
h=json.loads((folder/'road-history.json').read_text());roads=decode(json.loads((folder/'older-roads.json').read_text()))
alphas=tuple(x['alpha'] for x in json.loads((folder/'prepared-signatures.json').read_text()))
results=[]
for cls in (PreparedWorldMotion,Candidate):
 history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh']
 prepared=cls(*frames,*scenes,history,roads,rom)
 refs=[weakref.ref(prepared.pair),weakref.ref(prepared.roads)]
 cached=PrecomputedSourceWorldSamples(prepared,alphas)
 rows=[dict(buffers=signature(cached.sample(a))['buffers'],masks=[hashlib.sha256(bytes(x)).hexdigest() for x in cached.source_masks[a][:2]]) for a in alphas]
 results.append(rows)
 if cls is Candidate:
  assert all(ref() is None for ref in refs),'Closed heavy objects retained'
  assert prepared.rom is None and prepared.endpoint_roads==()
  assert prepared.construct_stages
  prepared.close()
  try:prepared.sample(.5)
  except ValueError:pass
  else:raise AssertionError('Closed interval sampled')
 else:assert all(ref() is not None for ref in refs)
 cached.close();history.close()
assert results[0]==results[1]
out=dict(result='PASS_CLOSED_WORLD_RELEASE_CAPTURED_PARITY',samples=len(alphas),buffers_and_source_masks=results[1],released_without_collection=True,scope='Actual captured precomputed buffers and source masks; no live cadence certification')
Path('work/camera/prototype-runs/closed-world-release-20261008.json').write_text(json.dumps(out,indent=2));print(out['result'])
