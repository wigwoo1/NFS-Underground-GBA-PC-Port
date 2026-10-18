"""Project retained model entry matrices against owned source ROM vertices."""
import ctypes as C,json,struct,collections
from pathlib import Path
from owned_graph_packet import GraphPacket
report=json.loads(Path('work/camera/prototype-runs/owned-native-1791278287813916200.json').read_text());trace=Path(report['model_pose_trace']);raw=trace.read_bytes()
folder=Path('work/camera/prototype-runs/fullscene-failure-1791277545474428100');state=GraphPacket.decode((folder/'older.graph.bin').read_bytes()).context[:256]
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
def read(address,size):
 offset=address-0x08000000;assert 0<=offset<=len(rom)-size;return rom[offset:offset+size]
base=struct.unpack_from('<I',state,124)[0];vertices=struct.unpack_from('<I',state,128)[0]
lib=C.CDLL('work/camera/native_model.dll');lib.nfs_model_project.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint32,C.c_int32,C.c_int32,C.c_void_p,C.c_void_p]
table=C.create_string_buffer(rom[0x627700:0x627700+0x6001*4]);rows=[];counts=collections.Counter()
for at in range(0,len(raw),292):
 h=struct.unpack_from('<8I',raw,at)
 if not 9945<=h[1]<=9965:continue
 source=raw[at+32:at+196];model=struct.unpack_from('<h',source,54)[0];matrix=raw[at+244:at+292]
 descriptor=read(base+(model-1)*40,40);n=struct.unpack_from('<H',descriptor,36)[0];local=read(vertices+struct.unpack_from('<I',descriptor)[0]*6,n*6)
 dest=C.create_string_buffer(n*4);ok=lib.nfs_model_project(matrix,local,n,128,120,80,table,dest)
 counts[(model,ok)]+=1;rows.append(dict(refresh=h[1],model=model,vertices=n,projection_success=ok,matrix=list(struct.unpack('<12i',matrix))))
assert rows
out=dict(scope='Captured model-entry matrices and descriptor base from same race; exact per-entry context/LOD capture still pending',counts=[dict(model=k[0],success=k[1],count=n) for k,n in sorted(counts.items())],rows=rows)
trace.with_suffix('.projection.json').write_text(json.dumps(out,indent=2));print(out['counts'])
