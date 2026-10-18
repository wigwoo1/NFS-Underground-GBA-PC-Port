"""Complete selector12 object/scratch behavior, original live-installed math; sound delivery seam only."""
from pathlib import Path
import ctypes as C,struct,random,sys,json
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
p=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,0x800000)]:u.mem_map(a,n)
u.mem_write(0x08000000,rom);d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t);Project=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_void_p,C.c_void_p);fn=d.nf_object_callback12_owned;fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,Read,C.c_void_p,C.c_void_p]
u.mem_write(0x03000000,(p/'native-endpoint-route-iwram.bin').read_bytes());counter_address=struct.unpack_from('<I',rom,0x23a0c)[0]
@Read
def read(ctx,a,out,n):
 try:C.memmove(out,bytes(u.mem_read(a,n)),n);return 1
 except Exception:return 0
original_sounds=[];original_projections=[];native_projections=[]
def hook(cpu,pc,n,ctx):
 if pc==0x08001268:original_sounds.append(cpu.reg_read(UC_ARM_REG_R0));cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))

u.hook_add(UC_HOOK_CODE,hook)
@Project
def project(ctx,state,obj):native_projections.append(C.string_at(obj,164));return 1
rng=random.Random(0x1fc7c);sound_events=0;states={}
for trial in range(500):
 state=bytearray(256);struct.pack_into('<I',state,16,0x02008000);struct.pack_into('<I',state,20,0x02001000);desc=bytearray(48);struct.pack_into('<H',desc,8,1);struct.pack_into('<H',desc,10,65535);struct.pack_into('<3h',desc,20,0,16384,0);struct.pack_into('<h',desc,38,rng.randrange(-200,201));vertex=bytearray(68);struct.pack_into('<h',vertex,56,rng.randrange(-200,201))
 obj=bytearray(rng.randbytes(164));mode=trial%5;struct.pack_into('<H',obj,74,mode);struct.pack_into('<H',obj,120,0);struct.pack_into('<h',obj,96,0 if trial%7==0 else rng.randrange(-32768,32768));struct.pack_into('<H',obj,108,rng.randrange(65536))
 struct.pack_into('<I',state,84,0x02009000);struct.pack_into('<I',state,252,0x0200b000);struct.pack_into('<I',obj,140,0x0200d000);camera=struct.pack('<12i',16384,0,0,0,16384,0,0,0,16384,0,0,0);scratch=rng.randbytes(3072);counter=[0,1,62,63,64][trial%5]
 for a,b in [(counter_address,struct.pack('<I',counter)),(0x02009000,camera),(0x0200b000,scratch),(0x0200d000,rng.randbytes(356)),(0x02000000,state),(0x02001000,desc),(0x02008000,vertex),(0x0200a000,obj)]:u.mem_write(a,bytes(b))
 original_sounds.clear();original_projections.clear();native_projections.clear()
 for reg,val in [(UC_ARM_REG_R0,0x02000000),(UC_ARM_REG_R1,0x0200a000),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)]:u.reg_write(reg,val)
 u.emu_start(0x0801fc7d,0x03006000,count=10000);assert u.reg_read(UC_ARM_REG_PC)==0x03006000 and u.reg_read(UC_ARM_REG_R0)==1
 native=C.create_string_buffer(bytes(obj),164);event=C.c_uint(123);ns=C.create_string_buffer(scratch,3072);nc=C.c_uint32(counter);assert fn(bytes(state),native,C.byref(nc),ns,read,None,C.byref(event));assert native.raw==bytes(u.mem_read(0x0200a000,164)),trial;assert ns.raw==bytes(u.mem_read(0x0200b000,3072)),trial;assert nc.value==struct.unpack('<I',bytes(u.mem_read(counter_address,4)))[0];assert original_sounds==([10] if event.value else []);sound_events+=event.value==10;states[mode]=states.get(mode,0)+1
@Read
def unavailable(ctx,a,out,n):return 0
broken=bytearray(obj);struct.pack_into('<H',broken,74,1);native=C.create_string_buffer(bytes(broken),164);event=C.c_uint(123);ns=C.create_string_buffer(scratch,3072);nc=C.c_uint32(0)
assert not fn(bytes(state),native,C.byref(nc),ns,unavailable,None,C.byref(event)) and native.raw==bytes(broken) and event.value==123 and ns.raw==scratch and nc.value==0
struct.pack_into('<H',broken,10,6);struct.pack_into('<h',broken,54,1);struct.pack_into('<h',broken,96,10)
for denied in [0x02009000,0x08623700]:
 @Read
 def limited(ctx,a,out,n):return 0 if (a==denied or (denied==0x08623700 and denied<=a<denied+16384)) else read(ctx,a,out,n)
 native=C.create_string_buffer(bytes(broken),164);event=C.c_uint(123);ns=C.create_string_buffer(scratch,3072);nc=C.c_uint32(0)
 assert not fn(bytes(state),native,C.byref(nc),ns,limited,None,C.byref(event)) and native.raw==bytes(broken) and event.value==123 and ns.raw==scratch and nc.value==0
report=dict(result='PASS',original_complete_callback_cases=500,state_cases=states,sound10_events=sound_events,atomic_rejections=3,scope='Full original selector12 including ground, damage, projection slots and actual installed ARM matrix code; only sound delivery stubbed. Object164bytes, scratch3072bytes, counter and requested sound events exact. Not yet integrated into sampled scene producer.')
(p/'object-callback-owned-tests.json').write_text(json.dumps(report,indent=2));print(report)
