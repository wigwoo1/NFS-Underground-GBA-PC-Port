import runpy,sys,struct,json
from pathlib import Path
sys.argv=['audit','work/camera/prototype-runs/fullscene-failure-1791284570990803400'];v=runpy.run_path('work/camera/audit_complete_model_transition.py')
from owned_motion_pairs import records
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();findings=[]
for endpoint,scene in enumerate(v['scenes']):
 visits=v['visits'][endpoint];models=[(i,row) for i,row in enumerate(records(v['frames'][endpoint])['records']) if row['kind']==3];base=struct.unpack_from('<I',scene.graph.context,124)[0]
 for index,row in models:
  desc=bytes(row['blocks'][1]);matches=[k for k,item in visits.items() if desc==rom[item['dispatch']['descriptor']-0x08000000:item['dispatch']['descriptor']-0x08000000+40]]
  variants=[k+1 for k in range(80) if desc==rom[base-0x08000000+k*40:base-0x08000000+(k+1)*40]]
  findings.append(dict(endpoint=endpoint,record=index,source_matches=matches,descriptor_variants=variants,visits=[dict(object=k,model=item['dispatch']['model'],variant=item['dispatch']['variant'],depth=item['depth']) for k,item in visits.items()]))
print(json.dumps(findings,indent=2))
