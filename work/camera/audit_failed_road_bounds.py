import sys,runpy,struct
from owned_endpoint_road_planner import EndpointRoadPlanner
from owned_endpoint_road_selection import endpoint_road_span_candidates
from pathlib import Path
v=runpy.run_path('work/camera/audit_complete_model_transition.py');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();h=EndpointRoadPlanner(rom,v['table'])
for scene in v['scenes']:
 _,_,memory,sources=h.assets.get(scene)
 for item in endpoint_road_span_candidates(scene,memory,sources,v['table'],include_empty=True):
  l,r,t,b=item['bounds']
  if not (0<=l<=r<=239 and 0<=t<=b<=159):print('INVALID_ROAD_CANDIDATE',scene.refresh,{k:value for k,value in item.items() if k!='source'})
h.close()
