import json,time,statistics,ctypes as C
from pathlib import Path
from unittest.mock import patch
import owned_closed_scene_memory as memory
folder=Path('work/camera/prototype-runs/profile-scene-1791315344561164600')
source=Path('work/camera/test_external_changed_parent_exit.py').read_text().split('gpu=C.CDLL')[0].replace("folder=Path('work/camera/prototype-runs/fullscene-failure-1791308040881565000')",'folder=Path('+repr(str(folder))+')')
exec(compile(source,'captured_profile_setup','exec'));prepared.close();history.close()
from owned_closed_scene_bulk_candidate import ClosedSceneMemory as Candidate
prior={'ClosedSceneMemory':memory.ClosedSceneMemory}
alphas=json.loads((folder/'capture.json').read_text())['alphas'];times={'before':[],'after':[]};reference=None
for repeat in range(8):
 for name,cls in ([('before',prior['ClosedSceneMemory']),('after',Candidate)] if repeat%2==0 else [('after',Candidate),('before',prior['ClosedSceneMemory'])]):
  memory._scene_memory_local.entries=[]
  with patch.object(memory,'ClosedSceneMemory',cls):
   started=time.perf_counter_ns();history=EndpointRoadPlanner(rom,table);prepared=None
   try:
    roads,_=history.plan(scenes[0].graph);prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
    samples=[prepared.sample(a) for a in alphas]
    times[name].append((time.perf_counter_ns()-started)/1e6)
    normalized=[(x[0],tuple(None if v is None else bytes(v) for v in x[1:4]),x[4]) for x in samples]
    if reference is None:reference=normalized
    else:assert normalized==reference
   finally:
    if prepared is not None:prepared.close()
    history.close()
result=dict(result='PASS_EXACT_REPLAY_OUTPUTS',alphas=alphas,rounds=8,median_ms={k:statistics.median(v) for k,v in times.items()},range_ms={k:[min(v),max(v)] for k,v in times.items()},scope='Interleaved replay with rebuilt initial planner; global caches may warm; not original live planner history or gameplay timing')
Path('outputs/nfsug-native-renderer/camera-research/checkpoints/all-successful-native-starvation-20261010/empty-extension-prepared-parity.json').write_text(json.dumps(result,indent=2));print(result)
