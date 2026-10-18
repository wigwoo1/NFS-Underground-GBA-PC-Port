"""Original object visibility predicate at captured opponent source boundaries."""
import sys,json,struct,ctypes as C
from pathlib import Path
from owned_closed_graph import ClosedGraph
from owned_model_sources import OwnedModelSources
from owned_motion_visibility import PortalMotionPair
from sample_owned_motion import PreparedMotionPair
r=json.loads(Path(sys.argv[1]).read_text());captures=r['model_scene_captures'];scenes=[ClosedGraph.decode(Path(x['graph']).read_bytes()) for x in captures];frames=[Path(x['frame']).read_bytes() for x in captures]
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();reciprocal=C.create_string_buffer(rom[0x627700:0x647700]);table=struct.unpack('<32768I',Path('work/camera/road-correction-reciprocal.bin').read_bytes()[:131072])
lib=C.CDLL(str(Path('work/camera/visibility-probe-wide.dll').resolve()));lib.nfs_visibility_object_branch_prepare.argtypes=[C.c_void_p]*7;lib.nfs_visibility_object_visible.argtypes=[C.c_void_p,C.c_void_p];out=[]
for e,(closed,capture) in enumerate(zip(scenes,captures)):
 sources=OwnedModelSources.decode(Path(capture['current-sources']).read_bytes(),closed);base=struct.unpack_from('<I',closed.graph.context,60)[0];source=sources.sources[base+164]
 other=1 if e==0 else e-1;a,b=sorted((e,other));pair=PortalMotionPair(scenes[a].graph,scenes[b].graph,table,PreparedMotionPair(frames[a],frames[b]));queue=pair.sample(int(e==b));regions=[q for q in queue if q[0]==23 and not q[5]&0x88]
 if not regions:
  out.append(dict(refresh=closed.refresh,source_refresh=closed.graph.refresh,visible=0,reason='no parent portal coverage'));continue
 assert len(regions)==1
 state=C.create_string_buffer(closed.graph.context[:256],256);xyz=(C.c_uint32*3)();branch=C.c_uint();child=C.create_string_buffer(16)
 assert lib.nfs_visibility_object_branch_prepare(state,source,struct.pack('<8H',*regions[0],65535),closed.graph.context[256:304],xyz,C.byref(branch),child)==1
 projection=closed.graph.context[304:336];params=(C.c_uint32*6)(xyz[1],xyz[2],struct.unpack_from('<I',projection,28)[0],struct.unpack_from('<h',projection,10)[0],struct.unpack_from('<H',state.raw,230)[0],struct.unpack_from('<H',state.raw,232)[0])
 visible=lib.nfs_visibility_object_visible(params,reciprocal)
 out.append(dict(refresh=closed.refresh,source_refresh=closed.graph.refresh,branch=branch.value,xyz=list(xyz),params=list(params),visible=visible))
Path(sys.argv[1]).with_suffix('.opponent-visibility.json').write_text(json.dumps(out,indent=2));print(out)
assert [x['visible'] for x in out]==[0,0,1,1], 'Original predicate does not reproduce appearance'
print('PASS recovered original object visibility matches absent/absent/present/present opponent draws')
