import ctypes as C,random,struct,json
from pathlib import Path
from owned_root_offset_queries import fixed_offset,fixed_queries,continuous_queries
from owned_graph_packet import GraphPacket
from owned_motion_visibility import pose_camera
from sample_owned_motion import PreparedMotionPair
rng=random.Random(19024);d=C.CDLL(str(Path('work/camera/visibility-probe-wide.dll').resolve()));d.nfs_visibility_offset.argtypes=[C.c_void_p,C.c_void_p]
for trial in range(1000):
 m=[rng.randrange(-2147483648,2147483648) for _ in range(12)];q=(C.c_uint32*12)(*[m[j*3+i]&0xffffffff for i in range(3) for j in range(3)],0,0,0);result=(C.c_uint32*3)();assert d.nfs_visibility_offset(q,result)
 assert fixed_offset(m)==tuple(C.c_int32(v).value for v in result)
folder=Path('work/camera/prototype-runs/fullscene-failure-1791274790496290000');a=GraphPacket.decode((folder/'older.graph.bin').read_bytes());b=GraphPacket.decode((folder/'newer.graph.bin').read_bytes());raw=[struct.unpack_from('<12i',g.context,256) for g in (a,b)];pair=PreparedMotionPair((folder/'older.frame.bin').read_bytes(),(folder/'newer.frame.bin').read_bytes());endpoints=tuple(pose_camera(p) for p in pair.arguments[2:4]);rows=[]
for alpha in (0,.25,.5,.6,.7,.75,1):
 camera=endpoints[int(alpha)] if alpha in (0,1) else tuple(pair.sample(alpha)[1]);queries=continuous_queries(*raw,endpoints,camera,alpha)
 if alpha in (0,1):assert queries==fixed_queries(raw[int(alpha)])
 rows.append(dict(alpha=alpha,queries=queries,forward_side=queries[0][2]-5600))
assert next(x for x in rows if x['alpha']==.6)['forward_side']<0 and next(x for x in rows if x['alpha']==.7)['forward_side']>0
for alpha in (float('nan'),-1,2):
 try:continuous_queries(*raw,endpoints,endpoints[0],alpha)
 except ValueError:pass
 else:raise AssertionError('Invalid alpha accepted')
Path('work/camera/root-offset-query-tests.json').write_text(json.dumps(dict(native_fixed_cases=1000,samples=rows,scope='Query component; original descriptor selection/fallback and fullscene root switching not yet implemented.'),indent=2))
print('PASS1000 original fixed-offset cases, exact captured query endpoints, rigid forward-query crossing between0.6and0.7, invalid alpha rejection')
