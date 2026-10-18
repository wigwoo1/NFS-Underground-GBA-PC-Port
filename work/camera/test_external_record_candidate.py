import json,struct,sys
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_model_sources import OwnedModelSources
from owned_motion_visibility import PortalMotionPair
from sample_owned_motion import PreparedMotionPair
from owned_external_record_candidate import external_record_candidate
from owned_motion_pairs import records
from owned_model_assets import model_palette_equivalent
p=Path(sys.argv[1]);r=json.loads(p.read_text());start=int(sys.argv[2]) if len(sys.argv)>2 else 1;captures=r['model_scene_captures'][start:start+2]
scenes=[ClosedGraph.decode(Path(c['graph']).read_bytes()) for c in captures];frames=[Path(c['frame']).read_bytes() for c in captures]
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072])
portal=PortalMotionPair(scenes[0].graph,scenes[1].graph,table,PreparedMotionPair(*frames));blocks=[]
for e,(scene,capture) in enumerate(zip(scenes,captures)):
 sources=OwnedModelSources.decode(Path(capture['current-sources']).read_bytes(),scene)
 region=next(q for q in portal.sample(e) if q[0]==23 and not q[5]&0x88)
 blocks.append(external_record_candidate(scene,sources,1,region,rom))
rows=records(frames[1])['records'];row=next(row for row in rows if row['kind']==3 and bytes(row['blocks'][2])==blocks[1][2])
assert all(blocks[1][i]==bytes(row['blocks'][i]) for i in range(11))
assert model_palette_equivalent(blocks[1],bytes(row['blocks'][11]))
assert all(blocks[0][i]==blocks[1][i] for i in (1,4,5,6,7,8,10))
p.with_suffix('.external-candidate.json').write_text(json.dumps(dict(complete_blocks=12,exact_newer=True,topology_equal=True,limitation='Candidate asset preparation only; original lifecycle and sampled clipping not yet integrated.'),indent=2))
print('PASS complete12-block external candidates; newer exact original geometry/material, topology stable')
