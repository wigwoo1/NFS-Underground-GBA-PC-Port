"""Repeated exact captured scene preparation; signature hashing outside timed region."""
import sys,json,time,statistics,hashlib
from pathlib import Path
candidate='--candidate' in sys.argv
if candidate:
 from install_combined_performance_candidate import install
 install()
from owned_road_record_diagnostic import decode
from owned_road_history_diagnostic import restore
from owned_sample_signature import signature
from owned_thread_cycles import read as cycles
folder=Path('outputs/nfsug-native-renderer/camera-research/checkpoints/exact-pair-10331-20261007/scene-inputs')
manifest=json.loads((folder.parent/'scene-input-manifest.json').read_text())['files']
assert all(hashlib.sha256((folder/name).read_bytes()).hexdigest()==info['sha256'] for name,info in manifest.items())
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
exec(compile(source,'exact_scene_setup','exec'));prepared.close();history.close()
import owned_sampled_world_frame as assembly
from owned_segmented_frame_candidate import SegmentedFrame
assembly.join_frame=SegmentedFrame.join
from owned_precomputed_segmented_samples import PrecomputedSourceWorldSamples
h=json.loads((folder/'road-history.json').read_text());roads=decode(json.loads((folder/'older-roads.json').read_text()));expected=json.loads((folder/'prepared-signatures.json').read_text());rows=[]
for i in range(20):
 history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh'];prepared=None;cached=None
 try:
  start=time.perf_counter_ns();cy=cycles();prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom);constructed=time.perf_counter_ns();cc=cycles();cached=PrecomputedSourceWorldSamples(prepared,tuple(x['alpha'] for x in expected),trace=True);end=time.perf_counter_ns();ec=cycles()
  actual=json.loads(json.dumps([dict(alpha=x['alpha'],signature=signature(cached.sample(x['alpha']))) for x in expected]));assert actual==expected
  rows.append(dict(round=i,construct_ms=(constructed-start)/1e6,precompute_ms=(end-constructed)/1e6,construct_cycles=cc-cy,precompute_cycles=ec-cc))
 finally:
  if cached is not None:cached.close()
  if prepared is not None:prepared.close()
  history.close()
result=dict(result='PASS_EXACT_INPUT_REPEATED_PREPARATION',candidate=candidate,rounds=rows,signature_samples_verified=len(expected)*len(rows),median_construct_ms=statistics.median(x['construct_ms'] for x in rows[4:]),median_precompute_ms=statistics.median(x['precompute_ms'] for x in rows[4:]),max_precompute_ms=max(x['precompute_ms'] for x in rows),scope='Owned scene files SHA256 checked; same saved planner scratch restored each round; sample signatures verified outside timed region. Warm graph caches, uncontrolled system load, no GPU presentation/timing/controller proof.')
Path(sys.argv[1]).write_text(json.dumps(result,indent=2));print({k:v for k,v in result.items() if k!='rounds'})
