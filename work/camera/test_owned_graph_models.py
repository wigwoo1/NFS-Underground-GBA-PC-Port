from pathlib import Path
import struct,json,collections
from owned_object_model_reference import descriptors
p=Path('work/camera');raw=(p/'owned-graph-models.bin').read_bytes();assert raw and len(raw)%580==0
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();seen=set();checks=[]
for pos in range(0,len(raw),580):
 h=struct.unpack_from('<8I',raw,pos);assert h[0]==0x314d4f4e and h[7]
 source=raw[pos+32:pos+196];state=raw[pos+196:pos+452];owned=raw[pos+500:pos+580]
 reference=descriptors(source,state)
 if reference is None:continue
 assert reference==(h[3],h[4],h[4]+40)
 assert (h[1],h[3]) not in seen;seen.add((h[1],h[3]))
 assert 0x08000000<=h[4] and h[4]+80<=0x08000000+len(rom);assert owned==rom[h[4]-0x08000000:h[4]-0x08000000+80]
 checks.append(dict(refresh=h[1],model=h[3],descriptor=h[4]))
r=dict(result='PASS_RAW_OBJECT_MODEL_REFERENCES',records=len(checks),models=sorted({x['model'] for x in checks}),checks=checks,scope='Both raw LOD descriptors verified; mesh topology/textures and live integration pending.')
(p/'owned-graph-models.json').write_text(json.dumps(r,indent=2));print(r['result'],r['records'],r['models'])
