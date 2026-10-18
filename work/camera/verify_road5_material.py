from pathlib import Path
import json,struct,hashlib
p=Path('work/camera');o=Path('outputs/nfsug-native-renderer/camera-research')
r=json.loads((o/'scene10-road5-original-invocation.json').read_text())[0];reads=r['reads'];state=bytes.fromhex(reads['state']);material=bytes.fromhex(reads['material']);rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
header=json.loads((o/'scene10-road5-source-audit.json').read_text())['raw_attributes_header'];assert reads['material_address']==header[4] and reads['animation_address']==header[5]
shift=struct.unpack_from('<H',material,26)[0];height=struct.unpack_from('<H',material,10)[0];assert (shift,height)==(header[1],header[2]);width=1<<shift
address=struct.unpack_from('<I',state)[0]+struct.unpack_from('<I',material,4)[0];packed=rom[address-0x08000000:address-0x08000000+width*height];assert len(packed)==width*height
indices=bytes(packed[y*width*2+x] for y in range(height//2) for x in range(width))
b=(p/'scene10-original-pose.packet').read_bytes();_,off,size=struct.unpack_from('<3I',b,44);w=b[off:off+size];count=struct.unpack_from('<I',w,4)[0];pos=8
for i in range(count):
 n,tw,th=struct.unpack_from('<3I',w,pos);pos+=12+n*40+tw*th*4
assert struct.unpack_from('<2I',w,pos)==(0x3149574e,count);pos+=8
for i in range(count):
 mode,length=struct.unpack_from('<2I',w,pos);pos+=8;payload=w[pos:pos+length];pos+=length
 if i==5:assert payload[:-288]==indices
report=dict(result='PASS',material_address=hex(reads['material_address']),animation_address=hex(reads['animation_address']),texture_address=hex(address),texture_size=[width,height//2],source_indices=sorted(set(indices)),indices_sha256=hashlib.sha256(indices).hexdigest(),original_draw_ordinal=r['ordinal'],scope='Retained material-plan resolution and immutable ROM packed-index equality. Palette color and original coverage/overdraw not established.')
(o/'scene10-road5-material-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
