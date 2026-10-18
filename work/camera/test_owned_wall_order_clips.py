from pathlib import Path
import struct,json
from owned_graph_packet import GraphPacket
from owned_wall_projection import projected
from owned_motion_pairs import records
p=Path('work/camera');raw=(p/'road-correction-reciprocal.bin').read_bytes();reciprocal=struct.unpack('<'+str(len(raw)//4)+'I',raw);checks=[]
for src,dst in zip((8754,8758,8762,8765,8769,8772,8776),(8758,8762,8766,8769,8773,8776,8780)):
 graph=GraphPacket.decode((p/f'graph-packets/{src}.ngp').read_bytes());draws,_=projected(graph,reciprocal);ordered=sorted(draws,key=lambda row:(-row[0],row[2].edge));selected=[row[2].vertices for row in ordered]
 captured=[row for row in records((p/f'motion-actual-scanline-assets/{dst}-native-complete-frame.bin').read_bytes())['records'] if row['kind']==2 and bytes(row['blocks'][0]) in selected]
 assert [bytes(row['blocks'][0]) for row in captured]==selected,(src,'Order mismatch')
 for draw,row in zip(ordered,captured):
  region=draw[1];expected=struct.pack('<4H',region[1],region[2],region[3],region[4]);assert bytes(row['blocks'][5])==expected,(src,draw[0],'Region clip mismatch',bytes(row['blocks'][5]),expected)
 checks.append(dict(refresh=src,walls=len(ordered),ordered_raw_edges_exact=True,clips_exact=True))
r=dict(result='PASS_OWNED_GRAPH_WALL_ORDER_CLIPS',checks=checks,scope='Independently selected graph edges ordered by original reverse region traversal then source edge order; all34 raw wall identities and region clips match original draws. Supplemental wall and deferred-pass samples pending.')
(p/'owned-wall-order-clips.json').write_text(json.dumps(r,indent=2));print(r)
