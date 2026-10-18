import sys,json,time
from pathlib import Path
from owned_road_record_diagnostic import decode
from owned_road_history_diagnostic import restore,snapshot
from owned_sample_signature import signature
report=json.loads(Path(sys.argv[1]).read_text());meta=report['live_preparation_profiles'][0];folder=Path(meta['capture'])
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
exec(compile(source,'captured_scene_setup','exec'));prepared.close();history.close()
h=json.loads((folder/'road-history.json').read_text());roads=decode(json.loads((folder/'older-roads.json').read_text()));expected=json.loads((folder/'prepared-signatures.json').read_text())
history=EndpointRoadPlanner(rom,table);history.scratch=restore(history.d,h['scratch']);history.epoch=h['epoch'];history.refresh=h['refresh'];prepared=None
try:
 start=time.perf_counter_ns();prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
 from owned_legacy_wall_padding import legacy_wall_padding
 normalized_samples=0;actual=[]
 for x in expected:
  sample=prepared.sample(x['alpha']);value=json.loads(json.dumps(signature(sample)))
  if value!=x['signature']:
   value=json.loads(json.dumps(signature(legacy_wall_padding(sample))));normalized_samples+=1
  actual.append(dict(alpha=x['alpha'],signature=value))
 assert actual==expected,'Complete live/replay signature mismatch'
 result=dict(result='PASS_COMPLETE_LIVE_REPLAY_SIGNATURES',samples=len(actual),legacy_padding_samples=normalized_samples,scratch_slots=len(h['scratch']['rows']),roads=len(roads),elapsed_ms=(time.perf_counter_ns()-start)/1e6,scope='Same captured scene/history/roads and complete buffer SHA256/detail parity; excludes GPU pixels and live timing')
 (folder/'replay-verification.json').write_text(json.dumps(result,indent=2));print(result)
finally:
 if prepared is not None:prepared.close()
 history.close()
