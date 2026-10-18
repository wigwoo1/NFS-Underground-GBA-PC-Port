"""Execute original complete wall inner loops; check skip vs remapped zero."""
from pathlib import Path
import json, struct, sys
sys.path.insert(0, 'work/pydeps')
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM
from unicorn.arm_const import *
from scene_batches import records
p = Path('work/camera')
rom = Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
cpu = Uc(UC_ARCH_ARM, UC_MODE_ARM)
cpu.mem_map(0x03000000, 0x10000)
cpu.mem_map(0x02000000, 0x40000)
cpu.mem_write(0x03000000, rom[0x71b0c:0x77b0c])
table = bytes((index*17 + shade*13) & 255 for index in range(256) for shade in range(16))
cpu.mem_write(0x02002000, table)
cases = skipped = zero_written = writes = 0
for lit in (False, True):
    for seed in range(256):
        texels = bytes(0 if (i+seed)%5==0 else (seed+i*19)&255 for i in range(32))
        texture = bytearray(128)
        texture[::4] = texels
        cpu.mem_write(0x02001000, bytes(texture))
        length = 1 + seed%32
        start = seed%32
        stride = 2 if seed%2 else 240
        original = bytes([0xad]) * (stride*length+8)
        cpu.mem_write(0x02008000, original)
        expected = bytearray(original)
        shade = seed%16
        for i in range(length):
            texel = texels[(start+i)%32]
            if texel:
                value = table[texel*16+shade] if lit else texel
                expected[i*stride] = value
                zero_written += value==0
                writes += 1
            else:
                skipped += 1
        registers = {UC_ARM_REG_R0:start<<15, UC_ARM_REG_R1:0x02008000,
                     UC_ARM_REG_R4:0x02001000, UC_ARM_REG_R5:length,
                     UC_ARM_REG_R6:2, UC_ARM_REG_R12:stride}
        if lit:
            registers.update({UC_ARM_REG_R9:(32<<15)-1, UC_ARM_REG_R10:15,
                              UC_ARM_REG_R7:0x02002000+shade, UC_ARM_REG_R8:1<<15})
            begin, end = 0x030053b0, 0x030053dc
        else:
            registers.update({UC_ARM_REG_R10:(32<<15)-1, UC_ARM_REG_R8:15,
                              UC_ARM_REG_R7:1<<15})
            begin, end = 0x03005460, 0x03005488
        for reg, value in registers.items():
            cpu.reg_write(reg, value)
        cpu.emu_start(begin, end, count=1000)
        actual = bytes(cpu.mem_read(0x02008000, len(original)))
        assert actual==expected, (lit, seed)
        cases += 1
assert skipped and zero_written
captured_tables = {bytes(e['blocks'][74][1]) for e in records(p/'shading.bin')
                   if e['pc']==0x03000304}
captured_zero_mappings = sum(t[index*16+shade]==0 for t in captured_tables
                             for index in range(1,256) for shade in range(16))
report = dict(result='PASS', original_loop_cases=cases, source_zero_skips=skipped,
              nonzero_source_writes=writes, shaded_output_zero_overwrites=zero_written,
              captured_tables=len(captured_tables),
              captured_nonzero_to_zero_mappings=captured_zero_mappings,
              scope='Original default lit/unlit wall inner loops with synthetic texture/shade table, stride2/240 and wrapped V. Source zero skips; nonzero mapped to zero overwrites. Full wall dispatch/LOD/extended mode and native GPU lit output-zero coverage remain unverified.')
(p/'wall-zero-writer-tests.json').write_text(json.dumps(report, indent=2))
print(report)
