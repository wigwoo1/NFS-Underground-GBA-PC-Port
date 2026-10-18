"""Standalone native builder versus exact original entry/exit memory."""
from pathlib import Path
import ctypes as C,json,struct
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
data=(root/'visibility-entry-200.bin').read_bytes();record_size=88+0x48000
header=struct.unpack_from('<22I',data);state_address=header[4]
ram=data[88:record_size];expected=data[record_size+88:]
regions=[(0x02000000,ram[:0x40000]),(0x03000000,ram[0x40000:]),(0x08000000,rom)]
def memory(address,size):
    for base,blob in regions:
        if base<=address and address+size<=base+len(blob):return blob[address-base:address-base+size]
    raise ValueError((hex(address),size))
state=memory(state_address,256);table,member=struct.unpack_from('<2I',state,0x60)
queue=memory(table,320);groups=memory(member,4096)
Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
requests=[];fail_at=None;errors=[]
@Reader
def read(context,address,destination,size):
    try:
        requests.append((address,size))
        if fail_at==len(requests):return 0
        C.memmove(destination,memory(address,size),size);return 1
    except Exception as error:errors.append(repr(error));return 0
fn=C.CDLL(str((root/'native_visibility.dll').resolve())).nfs_visibility_build
fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,Reader,C.c_void_p,C.c_void_p]
reciprocal=C.create_string_buffer(rom[0x627700:0x627700+32768*4])
s=C.create_string_buffer(state);q=C.create_string_buffer(queue);g=C.create_string_buffer(groups)
assert fn(s,q,g,read,None,reciprocal) and not errors
successful_reads=len(requests)
for address,actual in [(state_address,s.raw[:256]),(table,q.raw[:320]),(member,g.raw[:4096])]:
    offset=address-0x02000000 if address<0x03000000 else 0x40000+address-0x03000000
    assert actual==expected[offset:offset+len(actual)],hex(address)
# Inject every possible snapshot-read failure, including failures after a ring was processed.
for fail_at in range(1,successful_reads+1):
    requests.clear();s=C.create_string_buffer(state);q=C.create_string_buffer(queue);g=C.create_string_buffer(groups)
    assert not fn(s,q,g,read,None,reciprocal)
    assert (s.raw[:256],q.raw[:320],g.raw[:4096])==(state,queue,groups)
report=dict(result='PASS',standalone_native_builder=True,ARM_execution_used=False,
            captured_scene=header[5],state_bytes_exact=256,queue_bytes_exact=320,membership_bytes_exact=4096,
            snapshot_reads=successful_reads,atomic_read_failure_cases=successful_reads,
            scope='Complete original visibility builder from one exact coherent snapshot. Root initialization, object draw traversal, intermediate-pose validity and live renderer integration remain separate.')
(root/'visibility-builder-tests.json').write_text(json.dumps(report,indent=2));print(report)
