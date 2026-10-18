"""Selector12 core versus original Thumb with explicit projection/sound seams."""
from pathlib import Path
import ctypes as C,struct,random,sys,json
sys.path.insert(0,'work/pydeps')
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE
from unicorn.arm_const import *
p=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes();u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for a,n in [(0x02000000,0x40000),(0x03000000,0x10000),(0x08000000,0x800000)]:u.mem_map(a,n)
u.mem_write(0x08000000,rom);d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));Read=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t);Project=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_void_p,C.c_void_p);fn=d.nf_object_callback12;fn.argtypes=[C.c_void_p,C.c_void_p,Read,C.c_void_p,Project,C.c_void_p,C.c_void_p]
@Read
def read(ctx,a,out,n):
 try:C.memmove(out,bytes(u.mem_read(a,n)),n);return 1
 except Exception:return 0
original_sounds=[];original_projections=[];native_projections=[]
def hook(cpu,pc,n,ctx):
 if pc==0x08001268:original_sounds.append(cpu.reg_read(UC_ARM_REG_R0));cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
 if pc==0x080239c0:original_projections.append(bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R1),164)));cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
u.hook_add(UC_HOOK_CODE,hook)
@Project
def project(ctx,state,obj):native_projections.append(C.string_at(obj,164));return 1
rng=random.Random(0x1fc7c);sound_events=0;states={}
for trial in range(500):
 state=bytearray(256);struct.pack_into('<I',state,16,0x02008000);struct.pack_into('<I',state,20,0x02001000);desc=bytearray(48);struct.pack_into('<H',desc,8,1);struct.pack_into('<H',desc,10,65535);struct.pack_into('<3h',desc,20,0,16384,0);struct.pack_into('<h',desc,38,rng.randrange(-200,201));vertex=bytearray(68);struct.pack_into('<h',vertex,56,rng.randrange(-200,201))
 obj=bytearray(rng.randbytes(164));mode=trial%5;struct.pack_into('<H',obj,74,mode);struct.pack_into('<H',obj,120,0);struct.pack_into('<h',obj,96,0 if trial%7==0 else rng.randrange(-32768,32768));struct.pack_into('<H',obj,108,rng.randrange(65536))
 for a,b in [(0x02000000,state),(0x02001000,desc),(0x02008000,vertex),(0x0200a000,obj)]:u.mem_write(a,bytes(b))
 original_sounds.clear();original_projections.clear();native_projections.clear()
 for reg,val in [(UC_ARM_REG_R0,0x02000000),(UC_ARM_REG_R1,0x0200a000),(UC_ARM_REG_SP,0x03007d00),(UC_ARM_REG_LR,0x03006000)]:u.reg_write(reg,val)
 u.emu_start(0x0801fc7d,0x03006000,count=10000);assert u.reg_read(UC_ARM_REG_PC)==0x03006000 and u.reg_read(UC_ARM_REG_R0)==1
 native=C.create_string_buffer(bytes(obj),164);event=C.c_uint(123);assert fn(bytes(state),native,read,None,project,None,C.byref(event));assert native.raw==bytes(u.mem_read(0x0200a000,164)),trial;assert original_projections==native_projections and len(native_projections)==1;assert original_sounds==([10] if event.value else []);sound_events+=event.value==10;states[mode]=states.get(mode,0)+1
@Project
def reject(ctx,state,obj):C.memset(obj,0,164);return 0
native=C.create_string_buffer(bytes(obj),164);event=C.c_uint(123);assert not fn(bytes(state),native,read,None,reject,None,C.byref(event)) and native.raw==bytes(obj) and event.value==123
assert not fn(bytes(state),native,read,None,Project(),None,C.byref(event)) and native.raw==bytes(obj) and event.value==123
@Read
def unavailable(ctx,a,out,n):return 0
broken=bytearray(obj);struct.pack_into('<H',broken,74,1);native=C.create_string_buffer(bytes(broken),164);event=C.c_uint(123);assert not fn(bytes(state),native,unavailable,None,project,None,C.byref(event)) and native.raw==bytes(broken) and event.value==123
report=dict(result='PASS',original_thumb_cases=500,state_cases=states,sound10_events=sound_events,atomic_rejections=3,scope='Selector12 state/height/damage/angle core matches original with explicitly stubbed projection and sound delivery. Actual projection/global scratch and audio remain unimplemented.')
(p/'object-callback-tests.json').write_text(json.dumps(report,indent=2));print(report)
