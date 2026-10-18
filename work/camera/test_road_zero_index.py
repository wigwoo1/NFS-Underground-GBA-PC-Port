"""Original030056d8 road span: packed index bytes overwrite destination, including0."""
from pathlib import Path
import sys,struct,json
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
p=Path('work/camera');code=(p/'visibility-overflow-171-wide/iwram.bin').read_bytes();u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for base,size in [(0x02000000,0x40000),(0x03000000,0x10000),(0x06000000,0x20000)]:u.mem_map(base,size)
u.mem_write(0x03000000,code);global_address=struct.unpack_from('<I',code,0x5754)[0];assert global_address==0x03007098
cases=0;zero_cases=0
for pair in [b'\x00\x00',b'\x00\x01',b'\x7f\x00',b'\x00\xff',b'\xff\x7f']:
 for doubled in [0,1]:
  for count in range(1,18):
   for start in [0,2]:
    destination=0x06001000+start;u.mem_write(0x02001000,pair*32);u.mem_write(0x06001000,b'\xa5'*512);u.mem_write(global_address,struct.pack('<I',doubled))
    params=[3,7<<16,3<<16,0,0,0x02001000,destination,count,0,0,1<<16,0,0,0,0,0]
    u.mem_write(0x02002000,struct.pack('<16I',*params))
    for reg,value in [(UC_ARM_REG_R0,0x02002000),(UC_ARM_REG_SP,0x03007b00),(UC_ARM_REG_LR,0x03007c00)]:u.reg_write(reg,value)
    u.emu_start(0x030056d8,0x03007c00,count=3000);assert u.reg_read(UC_ARM_REG_PC)==0x03007c00
    expected=bytearray(b'\xa5'*512);expected[start:start+count*2]=pair*count
    if doubled:expected[start+240:start+240+count*2]=pair*count
    assert bytes(u.mem_read(0x06001000,512))==expected,(pair,doubled,count,start)
    cases+=1;zero_cases+=int(0 in pair)
report=dict(result='PASS',original_arm_cases=cases,zero_byte_cases=zero_cases,doubled_row_verified=True,adjacent_bytes_preserved=True,scope='Original affine packed road span030056d8 writes both indexed bytes including0; perspective03003190 and full-scene palette/coverage parity not verified here.')
(p/'road-zero-index-tests.json').write_text(json.dumps(report,indent=2));print(report)
