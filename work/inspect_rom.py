from pathlib import Path
import sys, struct, hashlib, re, json
sys.path.insert(0,str(Path(__file__).parent/'pydeps'))
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM,CS_MODE_THUMB
ROM=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba')
b=ROM.read_bytes()
out=Path('outputs/nfsug-research');out.mkdir(exist_ok=True,parents=True)
info={'file':str(ROM),'size':len(b),'sha256':hashlib.sha256(b).hexdigest(),'title':b[160:172].rstrip(b'\0').decode(),'game_code':b[172:176].decode(),'revision':b[188],'header_checksum_valid':((-sum(b[160:189])-0x19)&255)==b[189]}
(out/'rom-identity.json').write_text(json.dumps(info,indent=2))
strings=[{'address':hex(0x08000000+m.start()),'text':m.group().decode()} for m in re.finditer(rb'[ -~]{8,}',b) if re.search(rb'(?i)(pocketeers|track|engine|texture|\\.cpp|render)',m.group())]
(out/'strings.json').write_text(json.dumps(strings,indent=2))
def dis(addr,count=256,thumb=True,data=None,base=0x08000000):
 data=b if data is None else data
 md=Cs(CS_ARCH_ARM,CS_MODE_THUMB if thumb else CS_MODE_ARM)
 return '\n'.join(f'{i.address:08x}  {i.bytes.hex():10} {i.mnemonic:8} {i.op_str}' for i in md.disasm(data[addr-base:addr-base+count],addr))
if __name__=='__main__':
 print(json.dumps(info,indent=2))
 print(dis(int(sys.argv[1],0) if len(sys.argv)>1 else 0x08000220,int(sys.argv[2],0) if len(sys.argv)>2 else 512,len(sys.argv)<4 or sys.argv[3]!='arm'))
