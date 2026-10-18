import sys,json,struct,ctypes as C
from pathlib import Path
sys.path.insert(0,'work/camera')
from owned_graph_packet import GraphPacket
folder=Path('work/camera/prototype-runs/fullscene-failure-1791274790496290000');d=C.CDLL(str(Path('work/camera/visibility-probe-wide.dll').resolve()));d.nfs_visibility_offset.argtypes=[C.c_void_p,C.c_void_p];rows=[]
for label in ('older','newer'):
 g=GraphPacket.decode((folder/(label+'.graph.bin')).read_bytes());m=struct.unpack_from('<12i',g.context,256);query=[m[j*3+i]&0xffffffff for i in range(3) for j in range(3)]+[0,0,0];native=(C.c_uint32*12)(*query);offset=(C.c_uint32*3)();assert d.nfs_visibility_offset(native,offset)
 signed=lambda x:x if x<0x80000000 else x-0x100000000
 offs=list(map(signed,offset));position=(-m[9],-m[11]);plus=(position[0]+offs[0],position[1]+offs[2]);minus=(position[0]-offs[0],position[1]-offs[2]);rows.append(dict(label=label,offset=offs,plus=plus,minus=minus,plus_portal_side=plus[1]-5600,root=struct.unpack_from('<H',g.context,368)[0]))
sides=[r['plus_portal_side'] for r in rows];out=dict(samples=rows,plus_crossing_fraction=sides[0]/(sides[0]-sides[1]),scope='Recovered original paired offset query explains endpoint root transition; continuous spatial query and fullscene oracle pending.')
(folder/'root-offset-query-audit.json').write_text(json.dumps(out,indent=2));print(out)
