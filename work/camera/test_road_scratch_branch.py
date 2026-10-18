import json,struct
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_endpoint_road_planner import EndpointRoadPlanner
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());scenes=[ClosedGraph.decode(Path(x['graph']).read_bytes()) for x in r['wall_diagnostic_frames']];p=EndpointRoadPlanner(rom,table);checks=[]
try:
 try:p.fork()
 except ValueError:pass
 else:raise AssertionError('Uninitialized history fork accepted')
 p.plan(scenes[0])
 for i,c in enumerate(scenes[1:],1):
  fork=p.fork()
  try:
   expected,ed=fork.plan(c)
   if i+1<len(scenes):fork.plan(scenes[i+1])
  finally:fork.close()
  actual,ad=p.plan(c)
  assert [x['record'] for x in actual]==[x['record'] for x in expected] and ad==ed
  checks.append(dict(refresh=c.refresh,records=len(actual),branch_advanced_ahead=i+1<len(scenes)))
finally:p.close()
assert p.scratch is None
out=dict(result='PASS_ROAD_SCRATCH_BRANCH_ISOLATION',checks=checks,scope='15 independent branches preserve endpoint source history despite ahead-of-parent advancement; continuous road sampling pending')
Path('work/camera/road-scratch-branch-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],len(checks))
