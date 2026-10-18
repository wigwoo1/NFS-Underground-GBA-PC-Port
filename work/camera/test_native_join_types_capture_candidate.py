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
from owned_precomputed_decode_release_candidate import PrecomputedSourceWorldSamples
h=json.loads((folder/'road-history.json').read_text());roads=decode(json.loads((folder/'older-roads.json').read_text()))
alphas=tuple(x['alpha'] for x in json.loads((folder/'prepared-signatures.json').read_text()))
from owned_motion_pairs import _record_cache
import threading
foreign_ready=threading.Event();foreign_done=threading.Event();foreign_result=[]
def foreign():
 token=object();_record_cache.entries=[token];foreign_ready.set();foreign_done.wait(10);foreign_result.append(_record_cache.entries==[token])
thread=threading.Thread(target=foreign);thread.start();assert foreign_ready.wait(10)
import owned_sampled_world_frame as assembly
from owned_native_frame_join_types_candidate import join_frame,trace,helper
helper();assembly.join_frame=join_frame;assembly.join_frame_trace=trace
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
reference=json.loads(Path('work/camera/prototype-runs/closed-world-release-20261008.json').read_text())
assert results[1]==reference['buffers_and_source_masks']
class FailingPrepared:
 def close(self):self.closed=True
failing=FailingPrepared();_record_cache.entries=[object()]
try:PrecomputedSourceWorldSamples(failing,())
except ValueError:pass
else:raise AssertionError('Invalid sample count accepted')
assert failing.closed and _record_cache.entries==[]
assert _record_cache.entries==[]
foreign_done.set();thread.join(10);assert not thread.is_alive() and foreign_result==[True]
out=dict(result='PASS_NATIVE_JOIN_TYPES_CAPTURED_PARITY',samples=len(alphas),buffers_and_source_masks=results[1],released_without_collection=True,scope='Actual captured precomputed buffers and source masks; no live cadence certification')
Path('work/camera/prototype-runs/native-join-types-parity-20261008.json').write_text(json.dumps(out,indent=2));print(out['result'])



