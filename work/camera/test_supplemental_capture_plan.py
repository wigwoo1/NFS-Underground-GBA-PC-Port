import json,struct
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from owned_scene_bundle import chunks
from owned_supplemental_capture_plan import capture_plan,animation_plan
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());checks=[];verified=0
for frame in r['wall_diagnostic_frames']:
 closed=ClosedGraph.decode(Path(frame['graph']).read_bytes());plan=capture_plan(closed,rom)
 assert len({(p.kind,p.index) for p in plan})==len(plan)
 lookup={(p.kind,p.index):p for p in plan};materials={}
 supp=ClosedSupplements.decode(Path(frame['supplements']).read_bytes(),closed)
 for h,raw in chunks(supp.geometry,'supplements'):
  for i in range(h[4]):
   vertex=raw[976+i*140:1044+i*140];oi,mi=struct.unpack_from('<2H',vertex,42)
   for kind,index,slot in [('offset',oi,24),('material',mi,32)]:
    if index!=65535:
     p=lookup[kind,index];assert p.address==struct.unpack_from('<I',closed.graph.context,slot)[0]+index*32;verified+=1
   if mi!=65535:materials[mi]=raw[1076+i*140:1108+i*140]
 animations=animation_plan(materials,struct.unpack_from('<I',closed.graph.context,72)[0])
 assert all(p.size==8 for p in animations)
 checks.append(dict(refresh=closed.refresh,offset_reads=sum(p.kind=='offset' for p in plan),material_reads=sum(p.kind=='material' for p in plan),capture_bytes=sum(p.size for p in plan),captured_animation_reads=len(animations)))
out=dict(result='PASS_SUPPLEMENTAL_CAPTURE_PLAN',verified_invocation_references=verified,checks=checks,scope='Exact bounded offset/base-material/animation read requirements; producer capture and resolved texture closure pending.')
Path('work/camera/supplemental-capture-plan-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],verified,checks[0])
