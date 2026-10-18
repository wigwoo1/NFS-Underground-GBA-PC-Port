from pathlib import Path
import ctypes as C,json,struct,sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM
from unicorn.arm_const import *
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_select
fn.argtypes=[C.c_void_p,Reader,C.c_void_p,C.c_void_p]
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,len(rom))]:u.mem_map(a,n)
u.mem_write(0x08000000,rom)
reports=[]
def check(ram,stateaddr,label):
    def memory(addr,size):
        for base,data in [(0x02000000,ram[:0x40000]),(0x03000000,ram[0x40000:]),(0x08000000,rom)]:
            if base<=addr and addr+size<=base+len(data):return bytes(data[addr-base:addr-base+size])
        raise ValueError((hex(addr),size))
    calls=[];errors=[]
    @Reader
    def read(ctx,addr,dst,size):
        try:calls.append((addr,size));C.memmove(dst,memory(addr,size),size);return 1
        except Exception as e:errors.append(str(e));return 0
    u.mem_write(0x02000000,bytes(ram[:0x40000]));u.mem_write(0x03000000,bytes(ram[0x40000:]))
    for reg,val in [(UC_ARM_REG_R0,stateaddr),(UC_ARM_REG_SP,0x03007e00),(UC_ARM_REG_LR,0x03006000)]:u.reg_write(reg,val)
    u.emu_start(0x03000bd0,0x03006000,count=20000);assert u.reg_read(UC_ARM_REG_PC)==0x03006000
    state=C.create_string_buffer(memory(stateaddr,256));out=C.c_uint32(0xcccccccc)
    assert fn(state,read,None,C.byref(out)) and not errors,(label,errors)
    assert out.value==u.reg_read(UC_ARM_REG_R0),(label,out.value,u.reg_read(UC_ARM_REG_R0))
    assert state.raw[:256]==memory(stateaddr,256)
    for failindex in range(len(calls)):
        counter=[0]
        @Reader
        def fail(ctx,addr,dst,size):
            counter[0]+=1
            if counter[0]==failindex+1:return 0
            C.memmove(dst,memory(addr,size),size);return 1
        out.value=0xcccccccc
        assert not fn(state,fail,None,C.byref(out)) and out.value==0xcccccccc
    reports.append(dict(label=label,result=u.reg_read(UC_ARM_REG_R0),read_faults=len(calls)))

coverage=json.loads((root/'visibility-builder-coverage.json').read_text())
for case in coverage['cases']:
    for sample in case['samples']:
        blob=(root/'visibility-corpus'/sample['file']).read_bytes();header=struct.unpack_from('<22I',blob)
        check(bytearray(blob[88:88+0x48000]),header[4],sample['file'])
# Isolated synthetic two-region world tests every gate/redirect combination.
for material in [False,True]:
 for blocked in [False,True]:
  for linked in [False,True]:
   for height in [0,1]:
    for x,z in [(50,50),(150,50),(250,50),(100,50)]:
     ram=bytearray(0x48000);ram[0x40000:0x46000]=rom[0x71b0c:0x77b0c];state=0x02000000
     def put(off,fmt,*values):struct.pack_into(fmt,ram,off,*values)
     put(0x10,'<3I',0x02001000,0x02002000,0x02003000);put(0xc0,'<I',x);put(0xc8,'<I',z)
     for region in range(2):
      put(0x2000+region*48,'<2H',region*4,4);put(0x2008+region*48,'<H',height);put(0x2020+region*48,'<H',2 if linked else 65535)
      for i,(a,b) in enumerate([(0,0),(0,100),(100,100),(100,0)]):
       off=0x1000+(region*4+i)*68;put(off,'<2I',a+region*100,b)
       put(off+0x2a,'<H',0 if material else 65535);put(off+0x2e,'<H',0x1000 if blocked else 0);put(off+0x32,'<H',1 if region==0 else 65535)
     put(0x300e,'<H',0x1000 if blocked else 0)
     check(ram,state,f'synthetic:{material},{blocked},{linked},{height},{x},{z}')
report=dict(result='PASS',original_ARM_cases=len(reports),captured_state_cases=69,synthetic_cases=len(reports)-69,
 read_failure_checks=sum(r['read_faults'] for r in reports),results=sorted({r['result'] for r in reports}),
 scope='Local selector original-ARM comparison using captured state and synthetic branch fixtures. Captures occur at builder entry, not selection entry. Outer Thumb fallback and live intermediate-pose selection remain unverified.')
(root/'visibility-select-tests.json').write_text(json.dumps(report,indent=2));print(report)

