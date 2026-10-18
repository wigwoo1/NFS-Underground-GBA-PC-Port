"""Differential tests against the user's ROM. No ROM bytes are redistributed."""
from pathlib import Path
import ctypes as C
import json, random, struct, sys
sys.path.insert(0, str(Path('work/pydeps').resolve()))
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM
from unicorn.arm_const import *

rom = Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
u.mem_map(0x03000000, 0x10000)
u.mem_map(0x02000000, 0x40000)
u.mem_map(0x08000000, 0x800000)
u.mem_write(0x08000000, rom)
u.mem_write(0x03000000, rom[0x71b0c:0x71b0c+0x6000])
d = C.CDLL(str(Path('work/camera/native_projection.dll').resolve()))
d.nfs_camera_clip_edge.argtypes = [C.c_void_p,C.c_int,C.c_uint32,C.c_uint]
d.nfs_camera_project_x.argtypes = [C.c_void_p,C.c_uint32,C.c_int32,C.c_void_p]
d.nfs_camera_project_heights.argtypes = d.nfs_camera_project_x.argtypes
table = C.create_string_buffer(rom[0x627700:0x627700+0x6000*4])
r = random.Random(1638)
clip_counts = {}
for case in range(4000):
    original = r.randbytes(52)
    first = case & 1
    flags = (case & 2)*64
    t = [0,1,0x800000,0xffffff,0x1000000,0xffffffff][case%6] if case<120 else r.randrange(0x1000001)
    u.mem_write(0x02001000, original)
    for reg,value in [(UC_ARM_REG_R0,0x02001000),(UC_ARM_REG_R1,first),(UC_ARM_REG_R2,t),(UC_ARM_REG_R3,flags),(UC_ARM_REG_SP,0x03007f00),(UC_ARM_REG_LR,0x03007000)]:
        u.reg_write(reg,value)
    u.emu_start(0x03001638,0x03007000,count=1000)
    dst = C.create_string_buffer(original)
    d.nfs_camera_clip_edge(dst,first,t,flags)
    assert dst.raw[:52] == bytes(u.mem_read(0x02001000,52)), ('clip',case)
    key=f'endpoint_{0 if first else 1}_extra_attributes_{bool(flags)}'
    clip_counts[key]=clip_counts.get(key,0)+1
for case in range(4000):
    original = bytearray(r.randbytes(52))
    struct.pack_into('<hh',original,4,r.randrange(1,0x6000),r.randrange(1,0x6000))
    scale = r.randrange(1,65536)
    center = r.randint(-32768,32767)
    u.mem_write(0x02001000,bytes(original))
    stack=bytearray(128)
    struct.pack_into('<I',stack,0x4c,scale)
    struct.pack_into('<i',stack,0x54,center)
    u.mem_write(0x03007e00,bytes(stack))
    u.reg_write(UC_ARM_REG_SP,0x03007e00)
    u.reg_write(UC_ARM_REG_R5,0x02001000)
    u.emu_start(0x03001cb4,0x03001d24,count=100)
    dst=C.create_string_buffer(bytes(original))
    d.nfs_camera_project_x(dst,scale,center,table)
    assert dst.raw[:52] == bytes(u.mem_read(0x02001000,52)), ('projection',case)
for case in range(4000):
    original=bytearray(r.randbytes(52))
    depths=[r.randrange(1,0x6000),r.randrange(1,0x6000)]
    struct.pack_into('<hh',original,4,*depths)
    scale=r.randrange(1,65536)
    center=r.randint(-32768,32767)
    stack=bytearray(128)
    for offset,depth in [(4,depths[0]),(0,depths[1])]:
        reciprocal=struct.unpack_from('<I',rom,0x627700+depth*4)[0]
        struct.pack_into('<I',stack,offset,(scale*reciprocal)&0xffffffff)
    struct.pack_into('<i',stack,0x50,center)
    u.mem_write(0x02001000,bytes(original))
    u.mem_write(0x03007e00,bytes(stack))
    u.reg_write(UC_ARM_REG_SP,0x03007e00)
    u.reg_write(UC_ARM_REG_R5,0x02001000)
    u.emu_start(0x03001f30,0x03001fa4,count=100)
    dst=C.create_string_buffer(bytes(original))
    d.nfs_camera_project_heights(dst,scale,center,table)
    assert dst.raw[:52] == bytes(u.mem_read(0x02001000,52)), ('heights',case)
report={'result':'PASS','clip_cases':4000,'clip_coverage':clip_counts,'horizontal_projection_cases':4000,'vertical_projection_cases':4000,
        'scope':'Exact edge attribute clipping and horizontal/vertical edge projection blocks only. Full projection, scene reconstruction and shared-camera presentation are not integrated.'}
Path('work/camera/native-projection-tests.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
