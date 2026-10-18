from pathlib import Path
import ctypes as C,json,struct
from scene_batches import records
root=Path('work/camera');d=C.CDLL(str((root/'native_wall.dll').resolve()))
d.nfs_wall_shade_column.argtypes=[C.c_void_p,C.c_int,C.c_void_p]
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();table=C.create_string_buffer(rom[0x627700:0x627700+32768*4])
active=None;checked=0;walls=set()
for e in records(root/'shading-spans.bin'):
 if e['pc']==0x03000304:active=e
 if e['pc']!=0x03005320 or active is None:continue
 edge=C.create_string_buffer(active['blocks'][6][1]);dest=e['regs'][1]
 page=0x0600a000 if dest>=0x0600a000 else 0x06000000
 column=(dest-page)//2
 actual=struct.unpack_from('<h',e['blocks'][75][1],42)[0]
 expected=d.nfs_wall_shade_column(edge,column,table)
 assert expected==actual,(e['id'],column,expected,actual)
 checked+=1;walls.add(active['id'])
assert checked
report={'result':'PASS','live_shaded_columns':checked,'walls':len(walls),'scope':'Prepared-edge to original shade selection in one capture; varying source intensities, broader scenes and renderer integration remain to test.'}
(root/'wall-shade-column-tests.json').write_text(json.dumps(report,indent=2));print(report)
