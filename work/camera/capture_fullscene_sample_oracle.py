import json,struct,sys
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from owned_model_builder_inputs import OwnedModelBuilders
from owned_model_sources import OwnedModelSources
from owned_motion_scene import MotionScene
from owned_prepared_world_motion import PreparedWorldMotion
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_motion_pairs import records
r=json.loads(Path(sys.argv[1]).read_text());start=int(sys.argv[2]) if len(sys.argv)>2 else 1;captures=r['model_scene_captures'][start:start+2]
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);scenes=[];frames=[]
for c in captures:
 closed=ClosedGraph.decode(Path(c['graph']).read_bytes());scenes.append(MotionScene(closed,ClosedSupplements.decode(Path(c['supplements']).read_bytes(),closed,rom),OwnedModelBuilders(Path(c['builders']).read_bytes()),OwnedModelSources.decode(Path(c['current-sources']).read_bytes(),closed)));frames.append(Path(c['frame']).read_bytes())
history=EndpointRoadPlanner(rom,table);roads,_=history.plan(scenes[0].graph);prepared=PreparedWorldMotion(*frames,*scenes,history,roads,rom)
import time,hashlib
from test_scene_process_transport import digest
rows=[]
try:
 for i in range(101):
  started=time.perf_counter_ns();value=prepared.sample(i/100);completed=time.perf_counter_ns()
  rows.append(dict(alpha=i/100,digest=digest(value),wall_ns=completed-started,assembly_stages=prepared.pair._last_sample_stages))
 assert prepared.sample(0)[0]==frames[0] and prepared.sample(1)[0]==frames[1]
 output=Path(sys.argv[3]);output.write_text(json.dumps(dict(source_report=sys.argv[1],refreshes=[s.identity for s in scenes],samples=rows,scope='Fixed complete original scene sample fingerprints; same source interval as timing evidence, separately captured driving state; not full visual fidelity or live cadence proof'),indent=2));print('PASS101 fixed fullscene sample fingerprints and exact endpoints',output)
finally:prepared.close();history.close()
