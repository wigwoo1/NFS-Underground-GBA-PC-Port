from pathlib import Path
import struct,json
from owned_graph_packet import GraphPacket
from owned_motion_visibility import PortalMotionPair,sampled_root
from sample_owned_motion import PreparedMotionPair
folder=Path('work/camera/prototype-runs/fullscene-failure-1791274790496290000');a=GraphPacket.decode((folder/'older.graph.bin').read_bytes());b=GraphPacket.decode((folder/'newer.graph.bin').read_bytes());motion=PreparedMotionPair((folder/'older.frame.bin').read_bytes(),(folder/'newer.frame.bin').read_bytes());table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072]);portal=PortalMotionPair(a,b,table,motion);rows=[]
for i in range(101):
 alpha=i/100;camera=portal.endpoints[int(alpha)] if alpha in (0,1) else tuple(motion.sample(alpha)[1]);root=sampled_root(a,b,camera,alpha,portal.endpoints);regions=portal.sample(alpha);rows.append(dict(alpha=alpha,root=root,regions=len(regions)))
assert rows[0]['root']==19 and rows[-1]['root']==24 and rows[60]['root']==19 and rows[70]['root']==24
assert [x['root'] for x in rows]==sorted(x['root'] for x in rows)
Path('work/camera/root-transition-traversal-tests.json').write_text(json.dumps(rows,indent=2));print('PASS101 sampled original-query roots and complete portal traversals; endpoints19/24; single crossing')
