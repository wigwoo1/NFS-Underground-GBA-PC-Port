"""Replay original wall setup, bypassing only terminal pixel-writing routines."""
from pathlib import Path
import json, struct, sys
sys.path.insert(0, str(Path('work/pydeps').resolve()))
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *
from scene_batches import records

root = Path('work/camera')
rom = Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
walls = []
for event in records(root / 'shading-spans.bin'):
    if event['pc'] == 0x03000304:
        walls.append([event, []])
    elif event['pc'] in (0x03005320, 0x030053e8) and walls:
        walls[-1][1].append((event['pc'], *event['regs'][1:4]))
u = Uc(UC_ARCH_ARM, UC_MODE_ARM)
for address, size in [(0x02000000, 0x40000), (0x03000000, 0x10000),
                      (0x05000000, 0x1000), (0x06000000, 0x20000), (0x08000000, 0x800000)]:
    u.mem_map(address, size)
u.mem_write(0x08000000, rom)
registers = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
             UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
             UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
             UC_ARM_REG_R12, UC_ARM_REG_SP, UC_ARM_REG_LR]
actual = []
rejected = []
def hook(cpu, address, size, context):
    if address in (0x03005320, 0x030053e8):
        actual.append((address, *(cpu.reg_read(reg) for reg in registers[1:4])))
        cpu.reg_write(UC_ARM_REG_PC, cpu.reg_read(UC_ARM_REG_LR))
    elif address in (0x03000900, 0x03000b38):
        count = cpu.reg_read(UC_ARM_REG_R7 if address == 0x03000900 else UC_ARM_REG_R4)
        if count == 0 or count & 0x80000000:
            sp = cpu.reg_read(UC_ARM_REG_SP)
            dest = struct.unpack('<I', cpu.mem_read(sp + (0x10 if address == 0x03000900 else 8), 4))[0]
            rejected.append((dest, count))
u.hook_add(UC_HOOK_CODE, hook)
total = rejected_total = 0
examples = []
for event, expected in walls[:-1]:
    u.mem_write(0x02000000, bytes(0x40000))
    u.mem_write(0x03000000, bytes(0x10000))
    u.mem_write(0x03000000, rom[0x71b0c:0x77b0c])
    for address, data in event['blocks'].values():
        if data:
            u.mem_write(address, data)
    for reg, value in zip(registers, event['regs']):
        u.reg_write(reg, value)
    u.reg_write(UC_ARM_REG_LR, 0x03006000)
    actual.clear(); rejected.clear()
    u.emu_start(0x03000304, 0x03006000, count=100000)
    assert u.reg_read(UC_ARM_REG_PC) == 0x03006000, event['id']
    assert actual == expected, (event['id'], actual[:3], expected[:3])
    left, right = struct.unpack_from('<2h', event['blocks'][6][1])
    left >>= 1; right = (right+1) >> 1
    clip_left, clip_right = struct.unpack_from('<2H', event['blocks'][1][1], 0xe2)
    clip_left >>= 1; clip_right >>= 1
    count = right-left
    empty = count <= 1
    if left < clip_left:
        empty |= right < clip_left
        left = clip_left; count = right-left
    if right > clip_right:
        empty |= left > clip_right
        right = clip_right; count = right-left+1
    horizontal = [] if empty or count <= 1 else list(range(left, left+count))
    def column(dest):
        return (dest-(0x0600a000 if dest >= 0x0600a000 else 0x06000000))//2
    accounted = sorted([column(call[1]) for call in actual] + [column(dest) for dest, _ in rejected])
    assert accounted == horizontal, (event['id'], accounted, horizontal)
    total += len(actual); rejected_total += len(rejected)
    if rejected:
        examples.append(dict(event=event['id'], source=hex(event['blocks'][5][0]),
                             dispatched=len(actual), vertically_rejected=len(rejected)))
report = dict(result='PASS', walls=len(walls)-1, matched_dispatch_arguments=total,
              all_horizontal_columns_accounted_for=True,
              walls_with_vertical_rejection=len(examples), vertically_rejected_columns=rejected_total,
              rejection_examples=examples,
              scope='Original ARM setup replay, not a native implementation. Matches destination, starting V and row count; terminal pixel routines bypassed. Last potentially partial wall excluded.')
(root / 'wall-dispatch-replay-tests.json').write_text(json.dumps(report, indent=2))
print({key: value for key, value in report.items() if key != 'rejection_examples'})
