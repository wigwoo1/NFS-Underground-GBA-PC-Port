from pathlib import Path
import struct,json
from owned_graph_packet import GraphPacket
from owned_scene_bundle import SceneBundle
from owned_graph_wall_sources import wall_sources,supplemental_wall_sources
from owned_wall_region_candidates import source_flags,hidden,regions,candidates
from owned_motion_pairs import records
p=Path('work/camera');rb=(p/'road-correction-reciprocal.bin').read_bytes();reciprocal=struct.unpack('<'+str(len(rb)//4)+'I',rb);checks=[]
for src,dst in zip((8754,8758,8762,8765,8769,8772,8776),(8758,8762,8766,8769,8773,8776,8780)):
 graph=GraphPacket.decode((p/f'graph-packets/{src}.ngp').read_bytes());bundle=SceneBundle.decode((p/f'scene-bundles/{src}.nsb').read_bytes());sources=wall_sources(graph)+supplemental_wall_sources(bundle);owned_regions=regions(graph,reciprocal);potential=candidates(graph,reciprocal);count=0
 for row in records((p/f'motion-actual-scanline-assets/{dst}-native-complete-frame.bin').read_bytes())['records']:
  if row['kind']!=2:continue
  b=row['blocks'];matches=[w for w in sources if w.vertices==bytes(b[0]) and w.offsets==bytes(b[1])];assert matches
  w=matches[0];assert source_flags(w)==struct.unpack_from('<I',b[11],256)[0];assert not hidden(w);count+=1
 checks.append(dict(refresh=src,owned_regions=len(owned_regions),nonhidden_candidates=len(potential),executed_flags_exact=count))
assert sum(x['executed_flags_exact'] for x in checks)==35
r=dict(result='PASS_OWNED_WALL_SOURCE_FLAGS',checks=checks,scope='Original wall draw flags and hidden precedence derived from raw source/offsets; portal queue independently regenerated. Candidate list is not final projected wall dispatch.')
(p/'owned-wall-region-candidates.json').write_text(json.dumps(r,indent=2));print(r)
