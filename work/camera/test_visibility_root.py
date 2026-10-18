from pathlib import Path
import ctypes as C,json,struct
root=Path('work/camera');rom=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba').read_bytes()
Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
d=C.CDLL(str((root/'native_visibility.dll').resolve()));fn=d.nfs_visibility_root
fn.argtypes=[C.c_void_p,C.c_uint,Reader,C.c_void_p,C.c_void_p]
build=d.nfs_visibility_build;build.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,Reader,C.c_void_p,C.c_void_p]
reciprocal=C.create_string_buffer(rom[0x627700:0x627700+32768*4])
reports=[]
coverage=json.loads((root/'visibility-builder-coverage.json').read_text())
paths=[root/'visibility-corpus'/sample['file'] for case in coverage['cases'] for sample in case['samples']]
for path in paths:
    blob=path.read_bytes();size=88+0x48000;header=struct.unpack_from('<22I',blob)
    ram=blob[88:size];expected=blob[size+88:]
    def memory(address,size):
        for base,data in [(0x02000000,ram[:0x40000]),(0x03000000,ram[0x40000:]),(0x08000000,rom)]:
            if base<=address and address+size<=base+len(data):return data[address-base:address-base+size]
        raise ValueError((hex(address),size))
    errors=[]
    @Reader
    def read(context,address,destination,size):
        try:C.memmove(destination,memory(address,size),size);return 1
        except Exception as error:errors.append(repr(error));return 0
    state=memory(header[4],256);table,member=struct.unpack_from('<2I',state,0x60)
    selected=struct.unpack('<H',memory(0x03005d44,2))[0]
    s=C.create_string_buffer(state);seed=C.create_string_buffer(b'\xcc'*16)
    assert fn(s,selected,read,None,seed) and seed.raw[:16]==memory(table,16),(path.name,selected)
    # Rebuild using native seed, not the captured first queue record.
    q=C.create_string_buffer(seed.raw[:16]+memory(table+16,304));g=C.create_string_buffer(memory(member,4096))
    assert build(s,q,g,read,None,reciprocal) and not errors
    for address,actual in [(header[4],s.raw[:256]),(table,q.raw[:320]),(member,g.raw[:4096])]:
        off=address-0x02000000 if address<0x03000000 else 0x40000+address-0x03000000
        assert actual==expected[off:off+len(actual)],path.name
    reports.append(dict(file=path.name,selected=selected,root=struct.unpack_from('<H',seed.raw)[0]))
assert len(reports)==69
@Reader
def fail(context,address,destination,size):return 0
seed=C.create_string_buffer(b'\xcc'*16)
assert not fn(s,selected,fail,None,seed) and seed.raw[:16]==b'\xcc'*16
assert not fn(s,65535,read,None,seed) and seed.raw[:16]==b'\xcc'*16
report=dict(result='PASS',root_and_builder_exact_snapshots=len(reports),redirected_roots=sum(r['selected']!=r['root'] for r in reports),
            selected_descriptors=sorted({r['selected'] for r in reports}),invalid_or_read_failure_preserves_output=True,
            scope='Root initialization from captured selected-descriptor global and viewport, then native builder. Spatial root selection/fallback remains original game state.')
(root/'visibility-root-tests.json').write_text(json.dumps(report,indent=2));print(report)
