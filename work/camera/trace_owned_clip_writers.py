from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from capstone import Cs,CS_ARCH_ARM,CS_MODE_ARM
p=Path('work/camera');source=Path('work/race-iwram.bin');b=source.read_bytes();md=Cs(CS_ARCH_ARM,CS_MODE_ARM);md.skipdata=True
instructions=list(md.disasm(b[:0x6000],0x03000000));writers=[]
for i,x in enumerate(instructions):
 if x.mnemonic.startswith('strh') and any(v in x.op_str for v in ('#0xe2','#0xe4','#0xe6','#0xe8')):
  writers.append(dict(pc=hex(x.address),instruction=x.mnemonic+' '+x.op_str,context=[f'{y.address:08x} {y.mnemonic} {y.op_str}' for y in instructions[max(0,i-5):i+5]]))
assert len(writers)==10
r=dict(result='CLIP_WRITER_STATIC_DISCOVERY',source=str(source),sha256=hashlib.sha256(b).hexdigest(),writers=writers,scope='Static ARM IWRAM decode; runtime state-base/source-pointer ownership and upstream producer are not yet verified.')
(p/'owned-clip-writers.json').write_text(json.dumps(r,indent=2));print(r['result'],len(writers))
