"""Isolated original queue construction and geometry traversal oracle."""
from pathlib import Path
import json, struct, sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *
from scene_batches import batches
root=Path('work/camera')
rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
u=Uc(UC_ARCH_ARM,UC_MODE_ARM)
for address,size in [(0x02000000,0x40000),(0x03000000,0x10000),(0x05000000,0x1000),(0x06000000,0x20000),(0x08000000,0x800000)]:
    u.mem_map(address,size)
u.mem_write(0x08000000,rom)
def word(address):return struct.unpack('<I',u.mem_read(address,4))[0]
def half(address):return struct.unpack('<H',u.mem_read(address,2))[0]
def call(address):
    u.reg_write(UC_ARM_REG_SP,0x03007e00)
    u.reg_write(UC_ARM_REG_R0,0x030000c0)
    u.reg_write(UC_ARM_REG_LR,0x03006000)
    u.emu_start(address,0x03006000,count=2000000)
    assert u.reg_read(UC_ARM_REG_PC)==0x03006000
def restore(serial):
    for label,address in [('ewram',0x02000000),('iwram',0x03000000)]:
        u.mem_write(address,(root/f'visibility-scene-{serial}-{label}.bin').read_bytes())
reports=[]
for serial in (0,40,200):
    restore(serial);call(0x03004c74)
    count=half(0x030000c0+0xee);table=word(0x030000c0+0x60)
    actual=bytes(u.mem_read(table,count*16));expected_queue=(root/f'visibility-scene-{serial}.bin').read_bytes()
    reports.append(dict(scene=serial,count=count,queue_byte_identical=actual==expected_queue,
                        differing_bytes=sum(a!=b for a,b in zip(actual,expected_queue))+abs(len(actual)-len(expected_queue))))
    restore(serial)
    camera_address=word(0x030000c0+0x54)
    u.mem_write(camera_address,(root/f'visibility-scene-{serial}-render-camera.bin').read_bytes())
    call(0x03004c74)
    corrected_count=half(0x030000c0+0xee)
    corrected=bytes(u.mem_read(word(0x030000c0+0x60),corrected_count*16))
    reports[-1].update(render_camera_count=corrected_count,render_camera_queue_byte_identical=corrected==expected_queue)
    reports[-1]['render_camera_differences']=[dict(offset=i,actual=a,expected=b)
        for i,(a,b) in enumerate(zip(corrected,expected_queue)) if a!=b]
    restore(serial)
    u.mem_write(word(0x030000c0+0x54),(root/f'visibility-scene-{serial}-render-camera.bin').read_bytes())
    u.mem_write(word(0x030000c0+0x50),(root/f'visibility-scene-{serial}-render-projection.bin').read_bytes())
    call(0x03004c74)
    projection_count=half(0x030000c0+0xee)
    projection_queue=bytes(u.mem_read(word(0x030000c0+0x60),projection_count*16))
    reports[-1].update(render_projection_count=projection_count,render_projection_queue_byte_identical=projection_queue==expected_queue)
    history=(root/f'visibility-scene-{serial}-camera-history.bin').read_bytes()
    matches=[]
    for offset in range(0,len(history),116):
        sample=history[offset:offset+116];sample_step=struct.unpack_from('<I',sample)[0]
        restore(serial)
        u.mem_write(word(0x030000c0+0x54),sample[4:52])
        u.mem_write(word(0x030000c0+0x50),sample[52:116])
        call(0x03004c74)
        n=half(0x030000c0+0xee)
        if bytes(u.mem_read(word(0x030000c0+0x60),n*16))==expected_queue:matches.append(sample_step)
    reports[-1]['exact_history_steps']=matches
assert reports[0]['queue_byte_identical']
full_state_matches=[]
for step in range(786,792):
    for label,address in [('ewram',0x02000000),('iwram',0x03000000)]:
        u.mem_write(address,(root/f'visibility-step-{step}-{label}.bin').read_bytes())
    call(0x03004c74)
    n=half(0x030000c0+0xee)
    if bytes(u.mem_read(word(0x030000c0+0x60),n*16))==(root/'visibility-scene-200.bin').read_bytes():
        full_state_matches.append(step)
walls=[];groups=[];objects=[]
def hook(cpu,address,size,context):
    if address==0x030027f0:
        ptr=cpu.reg_read(UC_ARM_REG_R1)
        groups.append(dict(record=hex(ptr),caller_return=hex(cpu.reg_read(UC_ARM_REG_LR)),
                           fields=list(struct.unpack('<8H',cpu.mem_read(ptr,16)))))
    elif address==0x03002360:
        objects.append(dict(object=hex(cpu.reg_read(UC_ARM_REG_R7)),
                            record=list(struct.unpack('<8H',cpu.mem_read(cpu.reg_read(UC_ARM_REG_R1),16)))))
    elif address==0x03000304:
        state=cpu.reg_read(UC_ARM_REG_R1)
        walls.append(dict(source=hex(cpu.reg_read(UC_ARM_REG_R6)),
                          bounds=list(struct.unpack('<4H',cpu.mem_read(state+0xe2,8))),
                          group=groups[-1] if groups else None))
    elif address in (0x03005320,0x030053e8,0x030032f0):
        # Skip pixel-writing leaves; retain original traversal and wall setup.
        cpu.reg_write(UC_ARM_REG_PC,cpu.reg_read(UC_ARM_REG_LR))
restore(0)
u.hook_add(UC_HOOK_CODE,hook)
call(0x03004d5c)
expected=[dict(source=hex(e['blocks'][5][0]),bounds=list(struct.unpack_from('<4H',e['blocks'][1][1],0xe2)))
          for e in next(batches(root/'shading-spans.bin'))['events'] if e['pc']==0x03000304]
assert [dict(source=w['source'],bounds=w['bounds']) for w in walls]==expected
report=dict(result='PASS' if all(r['exact_history_steps'] for r in reports) else 'PARTIAL',
            queues=reports,scene0_walls_matched=len(walls),
            scene200_exact_full_state_steps=full_state_matches,
            arrow=[w for w in walls if w['source']=='0x857c6f4'],temporary_objects=objects,
            scope='Original ARM queue construction and traversal replay with terminal wall spans and road rendering bypassed. No native visibility implementation or interpolated-pose validation.')
(root/'visibility-replay-tests.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
