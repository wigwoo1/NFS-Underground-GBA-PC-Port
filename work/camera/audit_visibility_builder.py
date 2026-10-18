"""Bounded exact-entry coverage of the standalone native builder under steering."""
from pathlib import Path
import ctypes as C,hashlib,json,struct
root=Path('work').resolve();out=root/'camera';private=out/'visibility-corpus';private.mkdir(exist_ok=True)
rom_path=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba');rom=rom_path.read_bytes()
Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t)
Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
native=C.CDLL(str(out/'native_visibility.dll'));fn=native.nfs_visibility_build
fn.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,Reader,C.c_void_p,C.c_void_p]
reciprocal=C.create_string_buffer(rom[0x627700:0x627700+32768*4])
def verify(path):
    blob=path.read_bytes();record_size=88+0x48000;assert len(blob)==record_size*2
    first=struct.unpack_from('<22I',blob);last=struct.unpack_from('<22I',blob,record_size)
    assert first[:3]==(0x3151564e,0,0x03004c74) and last[:3]==(0x3151564e,1,0x03004d50)
    ram=blob[88:record_size];expected=blob[record_size+88:];errors=[]
    regions=[(0x02000000,ram[:0x40000]),(0x03000000,ram[0x40000:]),(0x08000000,rom)]
    def memory(address,size):
        for base,data in regions:
            if base<=address and address+size<=base+len(data):return data[address-base:address-base+size]
        raise ValueError((hex(address),size))
    @Reader
    def read(context,address,destination,size):
        try:C.memmove(destination,memory(address,size),size);return 1
        except Exception as error:errors.append(repr(error));return 0
    state=memory(first[4],256);table,member=struct.unpack_from('<2I',state,0x60)
    s=C.create_string_buffer(state);q=C.create_string_buffer(memory(table,320));g=C.create_string_buffer(memory(member,4096))
    accepted=fn(s,q,g,read,None,reciprocal);differences={}
    for name,address,actual in [('state',first[4],s.raw[:256]),('queue',table,q.raw[:320]),('groups',member,g.raw[:4096])]:
        offset=address-0x02000000 if address<0x03000000 else 0x40000+address-0x03000000
        differences[name]=sum(a!=b for a,b in zip(actual,expected[offset:offset+len(actual)]))
    count=struct.unpack_from('<H',expected,0x40000+first[4]-0x03000000+0xee)[0]
    records=expected[table-0x02000000:table-0x02000000+count*16];linked=[]
    descriptor_base=struct.unpack_from('<I',state,0x14)[0]
    for i in range(count):
        fields=struct.unpack_from('<8H',records,i*16)
        if fields[5]&0x80 and fields[7]<512:
            target=struct.unpack('<H',memory(descriptor_base+fields[7]*48+0x20,2))[0]
            if target==fields[0]:linked.append(i)
    return dict(file=path.name,scene=first[5],frame=first[3],queue_entries=count,accepted=bool(accepted),differences=differences,
                exact=bool(accepted) and not any(differences.values()) and not errors,read_errors=errors,linked_record_candidates=linked)
cases=[]
for name,steer in [('straight',0),('left',32),('right',16)]:
    runs=[];samples=[]
    for diagnostic in (False,True):
        d=C.CDLL(str(out/'visibility-probe.dll' if diagnostic else root/'nfsprobe.dll'))
        d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int]
        d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p];d.nf_dump.argtypes=[C.c_char_p,C.c_uint32,C.c_uint32]
        packets=[];errors=[]
        @Sink
        def receive(context,epoch,ptr,size):
            try:packets.append(hashlib.sha256(C.string_at(ptr,size)).hexdigest());return 1
            except Exception as error:errors.append(repr(error));return 0
        assert d.nf_init(str(rom_path).encode(),b'') and d.nf_state(str(root/'driving.state').encode(),0)
        try:
            assert d.nf_native_scene_sink(receive,None)
            if diagnostic:
                d.nf_visibility_capture.argtypes=[C.c_char_p,C.c_uint]
                target=private/f'{name}-00.bin';assert d.nf_visibility_capture(str(target).encode(),0)
            for frame in range(900):
                d.nf_frame(1|(steer if 180<=frame<720 else 0))
                if diagnostic and len(samples)<24:
                    status=d.nf_visibility_status();assert status!=3
                    if status==2:
                        samples.append(verify(target))
                        if len(samples)<24:
                            target=private/f'{name}-{len(samples):02d}.bin';assert d.nf_visibility_capture(str(target).encode(),9)
                        else:d.nf_visibility_capture(None,0)
            memory=[]
            for label,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000),('vram',0x06000000,0x18000)]:
                path=private/f'{name}-{diagnostic}-{label}.bin';d.nf_dump(str(path).encode(),address,size)
                memory.append(hashlib.sha256(path.read_bytes()).hexdigest())
            assert not errors;runs.append((packets,memory))
        finally:d.nf_close()
    assert runs[0]==runs[1]
    cases.append(dict(case=name,packets=len(runs[0][0]),capture_noninvasive=True,samples=samples))
    print(name,len(samples),'exact',sum(s['exact'] for s in samples),flush=True)
all_samples=[s for c in cases for s in c['samples']]
report=dict(result='PASS' if all(s['exact'] for s in all_samples) else 'FAIL',cases=cases,
            exact_snapshots=sum(s['exact'] for s in all_samples),total_snapshots=len(all_samples),
            positive_link_candidates=sum(bool(s['linked_record_candidates']) for s in all_samples),
            scope='Scripted single-race snapshot coverage; native builder runs without ARM. Linked records are candidates pending original-call confirmation. No intermediate-pose or live-renderer validation.')
(out/'visibility-builder-coverage.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='cases'})
assert report['result']=='PASS'
