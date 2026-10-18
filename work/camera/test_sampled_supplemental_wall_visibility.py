import json,struct
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_closed_supplements import ClosedSupplements
from owned_complete_supplemental_candidates import CompleteSupplementalCandidates
from owned_complete_supplemental_projection import projection_input
from owned_continuous_wall_visibility import sampled_edge,select_wall
from sample_owned_motion import PreparedMotionPair
from owned_motion_visibility import PortalMotionPair
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);r=json.loads(Path('work/camera/prototype-runs/owned-native-1791267744113946700.json').read_text());checks=[];maximum=0
for fa,fb in zip(r['wall_diagnostic_frames'],r['wall_diagnostic_frames'][1:]):
 a=ClosedGraph.decode(Path(fa['graph']).read_bytes());b=ClosedGraph.decode(Path(fb['graph']).read_bytes());sa=ClosedSupplements.decode(Path(fa['supplements']).read_bytes(),a);sb=ClosedSupplements.decode(Path(fb['supplements']).read_bytes(),b)
 motion=PreparedMotionPair(Path(fa['regenerated']).read_bytes(),Path(fb['regenerated']).read_bytes());portal=PortalMotionPair(a.graph,b.graph,table,motion);pair=CompleteSupplementalCandidates(a,b,sa,sb,portal,rom);samples=[]
 for alpha in (.001,.25,.5,.75,.999):
  _,camera,_=motion.sample(alpha);visible=0;total=0
  for c in pair.sample(alpha):
   raw,sources=projection_input(a,sa,rom,c.descriptor,(0,239,0,159),palette_required=False);n=len(sources);ring=b''.join(raw[976+i*140:1044+i*140] for i in range(n))
   for w in sources:
    edge=sampled_edge(w,ring,a.graph.context[256:304],b.graph.context[256:304],camera,portal.endpoints,alpha)
    if edge is None:continue
    base=raw[1076+w.edge*140:1108+w.edge*140];out=select_wall(w,raw[32:80],edge,a.graph.context[304:368],c.bounds,base,table);total+=1;visible+=out.visible
  samples.append(dict(alpha=alpha,candidates=total,visible=visible))
 for endpoint,near in ((0,1e-8),(1,1-1e-8)):
  for c in pair.sample(endpoint):
   scene,supp=(a,sa) if endpoint==0 else (b,sb);raw,sources=projection_input(scene,supp,rom,c.descriptor,c.bounds,palette_required=False);ring=b''.join(raw[976+i*140:1044+i*140] for i in range(len(sources)));_,camera,_=motion.sample(near)
   for w in sources:
    exact=sampled_edge(w,ring,a.graph.context[256:304],b.graph.context[256:304],(),portal.endpoints,endpoint);adjacent=sampled_edge(w,ring,a.graph.context[256:304],b.graph.context[256:304],camera,portal.endpoints,near)
    if exact is not None and adjacent is not None:maximum=max(maximum,max(abs(x-y) for x,y in zip(exact,adjacent)))
 checks.append(dict(older=a.refresh,newer=b.refresh,samples=samples))
assert maximum<1e-4
out=dict(result='PASS_SAMPLED_SUPPLEMENTAL_WALL_VISIBILITY',intervals=len(checks),maximum_near_endpoint_camera_space_error=maximum,checks=checks,scope='Fractional clips and corrected rigid camera-space surface selection; intermediate oracle, GPU insertion and complete cross-kind ordering pending.')
Path('work/camera/sampled-supplemental-wall-visibility-tests.json').write_text(json.dumps(out,indent=2));print(out['result'],maximum)

