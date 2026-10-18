from pathlib import Path
import struct,json
from owned_graph_packet import GraphPacket
from owned_scene_bundle import SceneBundle,chunks
from owned_graph_wall_sources import supplemental_wall_sources
from owned_wall_projection import projected
from owned_motion_pairs import records
p=Path('work/camera');raw=(p/'road-correction-reciprocal.bin').read_bytes();reciprocal=struct.unpack('<'+str(len(raw)//4)+'I',raw);checks=[];selected_total=0
for src,dst in zip((8754,8758,8762,8765,8769,8772,8776),(8758,8762,8766,8769,8773,8776,8780)):
 g=GraphPacket.decode((p/f'graph-packets/{src}.ngp').read_bytes());bundle=SceneBundle.decode((p/f'scene-bundles/{src}.nsb').read_bytes());sources=supplemental_wall_sources(bundle);supp=[]
 for h,data in chunks(bundle.supplements,'supplements'):
  candidates=[w for w in sources if w.descriptor==h[3]]
  # Descriptor may appear in separate calls: raw source edge identity disambiguates.
  ring=b''.join(data[976+i*140:1044+i*140] for i in range(h[4]));candidates=[w for w in candidates if w.vertices[:68] in [ring[i*68:(i+1)*68] for i in range(h[4])]]
  draws,stats=projected(g,reciprocal,(data,candidates));supp.extend(draws)
 graph_draws,_=projected(g,reciprocal);selected=[x[2].vertices for x in graph_draws+tuple(supp)];original=[row for row in records((p/f'motion-actual-scanline-assets/{dst}-native-complete-frame.bin').read_bytes())['records'] if row['kind']==2]
 assert sorted(selected)==sorted(bytes(row['blocks'][0]) for row in original),(src,'Complete wall selection mismatch',len(selected),len(original))
 for draw in supp:
  matches=[row for row in original if bytes(row['blocks'][0])==draw[2].vertices];assert len(matches)==1
  assert bytes(matches[0]['blocks'][5])==struct.pack('<4H',*draw[1][1:5])
 selected_total+=len(supp);checks.append(dict(refresh=src,supplemental_calls=len(list(chunks(bundle.supplements,'supplements'))),supplemental_selected=len(supp),all_walls=len(selected)))
assert selected_total==1
r=dict(result='PASS_OWNED_SUPPLEMENTAL_WALL_SELECTION',checks=checks,scope='Complete graph plus supplemental raw wall identity multiplicity and supplemental region clip match original35 draws. Supplemental call region retained owned snapshot; derivation from object dispatch and cross-kind order pending.')
(p/'owned-supplemental-wall-selection.json').write_text(json.dumps(r,indent=2));print(r)
