import runpy,sys
from pathlib import Path
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_motion_pairs import records
v=runpy.run_path('work/camera/audit_complete_model_transition.py');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();history=EndpointRoadPlanner(rom,v['table'])
try:
 history.plan(v['scenes'][0]);fork=history.fork()
 try:
  actual,details=history.plan(v['scenes'][1]);repeat,other=fork.plan(v['scenes'][1])
  empty=[row for row in details if row['empty_interval']]
  assert len(empty)==1 and empty[0]['descriptor']==27 and empty[0]['bounds']==(2,0,0,158)
  assert empty[0]['runs']==0 and empty[0]['missing']==0
  assert details==other and [r['record'] for r in actual]==[r['record'] for r in repeat]
  assert all(not (r['descriptor']==27 and r['ordinal']==1) for r in actual)
  assert history.refresh==v['scenes'][1].refresh and history.scratch
  print('PASS original zero-run empty road, scratch history advanced, deterministic fork and no invalid GPU submission',empty)
 finally:fork.close()
finally:history.close()
