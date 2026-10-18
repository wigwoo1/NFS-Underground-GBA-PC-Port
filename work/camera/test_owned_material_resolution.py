from pathlib import Path
import struct,json
from owned_material_resolution import resolve
p=Path('work/camera');raw=(p/'owned-material-resolution.bin').read_bytes();assert raw and len(raw)%152==0
checks=[]
for pos in range(0,len(raw),152):
 h=struct.unpack_from('<8I',raw,pos);assert h[0]==0x31524d4e
 base=raw[pos+32:pos+64];animation=raw[pos+64:pos+72];resolved=raw[pos+72:pos+104];material=raw[pos+104:pos+152]
 phase=struct.unpack_from('<H',animation,2)[0];assert h[6]==h[5]+phase*32
 shift=struct.unpack_from('<H',resolved,26)[0];height=struct.unpack_from('<H',resolved,10)[0];address=(h[4]+struct.unpack_from('<I',resolved,4)[0])&0xffffffff
 metadata=resolve(0,animation,{phase:resolved},h[4]);assert (metadata['shift'],metadata['height'],metadata['address'])==(shift,height,address)
 actual=struct.unpack_from('<HHI',material,36);assert actual==(shift,height,address),(h[1],actual,(shift,height,address))
 checks.append(dict(refresh=h[1],phase=phase,shift=shift,height=height,texture_address=address))
r=dict(result='PASS_RAW_WALL_MATERIAL_RESOLUTION',records=len(checks),checks=checks,scope='Executed material address/dimensions match raw resolution; full potential face texture payload ownership pending.')
(p/'owned-material-resolution.json').write_text(json.dumps(r,indent=2));print(r['result'],len(checks))
