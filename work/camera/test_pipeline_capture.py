"""Capture the actual offset matrix and composed selection sequence."""
from pathlib import Path
import ctypes as C, hashlib, json, struct, sys
sys.path.insert(0,str(Path('work/pydeps').resolve()))
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
root=Path('work').resolve();out=root/'camera'
corpus=out/'pipeline-corpus';corpus.mkdir(exist_ok=True)
rom_path=Path('G:/EXTRA DATA DRIVE/Desktop/Emulators/GBA/GBA ROMS/Need for Speed - Underground (USA, Europe) (En,Fr,De,It).gba')
Sink=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint64,C.c_void_p,C.c_size_t)
def run(path,diagnostic):
    d=C.CDLL(str(path));packets=[];errors=[];identities=[]
    d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_state.argtypes=[C.c_char_p,C.c_int]
    d.nf_dump.argtypes=[C.c_char_p,C.c_uint32,C.c_uint32];d.nf_native_scene_sink.argtypes=[Sink,C.c_void_p]
    @Sink
    def receive(context,epoch,ptr,size):
        try:
            packet=C.string_at(ptr,size);header=struct.unpack_from('<8I',packet)
            assert header[0]==0x3150534e and header[2]==size
            identities.append(dict(epoch=epoch,serial=header[4],begin=header[5],end=header[6]))
            packets.append(hashlib.sha256(packet).hexdigest());return 1
        except Exception as error:errors.append(repr(error));return 0
    assert d.nf_init(str(rom_path).encode(),b'') and d.nf_state(str(root/'driving.state').encode(),0)
    try:
        assert d.nf_native_scene_sink(receive,None)
        completed=[]
        if diagnostic:
            d.nf_visibility_pipeline_capture.argtypes=[C.c_char_p,C.c_uint]
            def arm(index):
                assert d.nf_visibility_pipeline_capture(str(corpus/f'select-{index:02}.bin').encode(),6)
            arm(0)
        for frame in range(850):
            d.nf_frame(1 | (32 if 180<=frame<500 else 16 if 500<=frame<720 else 0))
            if diagnostic and d.nf_visibility_status()==4 and len(completed)<24:
                completed.append(f'select-{len(completed):02}.bin')
                if len(completed)<24:arm(len(completed))
        if diagnostic:
            assert len(completed)==24,len(completed)
            (out/'pipeline-capture-manifest.json').write_text(json.dumps(completed,indent=2))
        memory=[]
        for label,address,size in [('ewram',0x02000000,0x40000),('iwram',0x03000000,0x8000),('vram',0x06000000,0x18000)]:
            target=out/f'pipeline-capture-{diagnostic}-{label}.bin'
            d.nf_dump(str(target).encode(),address,size);memory.append(hashlib.sha256(target.read_bytes()).hexdigest())
        assert not errors
        if diagnostic:(out/'pipeline-packet-identities.json').write_text(json.dumps(identities,indent=2))
        return packets,memory
    finally:d.nf_close()
baseline=run(root/'nfsprobe.dll',False);captured=run(out/'visibility-probe.dll',True)
assert baseline==captured
Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
dll=C.CDLL(str(out/'native_visibility.dll'));query=dll.nfs_visibility_query;build=dll.nfs_visibility_build_pair
query.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,Reader,C.c_void_p,C.c_void_p]
build.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,Reader,C.c_void_p,C.c_void_p]
rom=rom_path.read_bytes();reciprocal=C.create_string_buffer(rom[0x627700:0x627700+32768*4]);reports=[]
for name in json.loads((out/'pipeline-capture-manifest.json').read_text()):
 data=(corpus/name).read_bytes();stride=88+0x48000;assert len(data)==stride*4
 headers=[struct.unpack_from('<22I',data,i*stride) for i in range(4)]
 snapshots=[data[i*stride+88:(i+1)*stride] for i in range(4)]
 assert [h[1] for h in headers]==list(range(4))
 assert [h[2] for h in headers]==[0x08002cb4,0x08002d92,0x03004c74,0x03004d50]
 assert len({h[4] for h in headers})==1 and len({h[5] for h in headers})==1
 def memory(stage,addr,n):
  ram=snapshots[stage]
  for base,chunk in [(0x02000000,ram[:0x40000]),(0x03000000,ram[0x40000:]),(0x08000000,rom)]:
   if base<=addr and addr+n<=base+len(chunk):return chunk[addr-base:addr-base+n]
  raise ValueError((stage,hex(addr),n))
 def word(stage,addr):return struct.unpack('<I',memory(stage,addr,4))[0]
 def half(stage,addr):return struct.unpack('<H',memory(stage,addr,2))[0]
 stage=[0];reads=[];errors=[]
 @Reader
 def read(ctx,addr,dst,n):
  try:reads.append((stage[0],addr,n));C.memmove(dst,memory(stage[0],addr,n),n);return 1
  except Exception as e:errors.append(str(e));return 0
 h=headers[0];stateaddr=h[4];sp=h[19];matrix_address=word(0,sp+0x98);recovery_object=word(0,sp+0xa4)
 matrix=(C.c_uint32*12)(*struct.unpack('<12I',memory(0,matrix_address,48)))
 base=(C.c_uint32*2)(h[7],h[6]);selected=C.c_uint32(half(0,0x03005d44));pair=(C.c_uint32*2)()
 state=C.create_string_buffer(memory(0,stateaddr,256));recovery=half(0,recovery_object+0x78)
 assert query(state,C.byref(selected),recovery,base,matrix,read,None,pair) and not errors
 assert list(pair)==[headers[1][13],headers[1][15]]
 assert state.raw[:256]==memory(1,stateaddr,256) and selected.value==half(1,0x03005d44)
 query_reads=list(reads);reads.clear();stage[0]=2
 state=C.create_string_buffer(memory(2,stateaddr,256));table=word(2,stateaddr+0x60);members=word(2,stateaddr+0x64)
 queue=C.create_string_buffer(b'\xcc'*16+memory(2,table+16,304));groups=C.create_string_buffer(memory(2,members,4096))
 assert build(state,queue,groups,pair,C.byref(selected),read,None,reciprocal) and not errors
 assert state.raw[:256]==memory(3,stateaddr,256)
 assert queue.raw[:320]==memory(3,table,320) and groups.raw[:4096]==memory(3,members,4096)
 assert selected.value==half(3,0x03005d44)
 changed_query_reads=[(hex(addr),n) for _,addr,n in query_reads if memory(0,addr,n)!=memory(2,addr,n)]
 changed_builder_reads=[(hex(addr),n) for _,addr,n in reads if memory(0,addr,n)!=memory(2,addr,n)]
 queue_tail_changed=memory(0,table+16,304)!=memory(2,table+16,304)
 changes=[i for i,(a,b) in enumerate(zip(memory(1,stateaddr,256),memory(2,stateaddr,256))) if a!=b]
 reports.append(dict(file=name,frames=[h[3] for h in headers],scene=headers[0][5],pair=list(pair),recovery_object=hex(recovery_object),recovery_region=recovery,
  changed_query_geometry_reads=changed_query_reads,changed_builder_reads=changed_builder_reads,queue_tail_changed=queue_tail_changed,interstage_state_byte_offsets=changes))
report=dict(result='PASS',coherent_four_boundary_captures=len(reports),scene_packets_compared=len(baseline[0]),packet_hashes_and_final_ram_identical=True,
 native_query_and_native_builder_match_original=True,query_geometry_changes=sum(len(r['changed_query_geometry_reads']) for r in reports),
 interstage_changed_state_offsets=sorted({i for r in reports for i in r['interstage_state_byte_offsets']}),
 builder_input_changes=sum(len(r['changed_builder_reads']) for r in reports),queue_tail_changes=sum(r['queue_tail_changed'] for r in reports),
 recovery_objects=sorted({r['recovery_object'] for r in reports}),samples=reports,
 scope='Query and builder verified in the same original update with respective exact snapshots. Interstage state/setup remains original; not yet one fully native pipeline or intermediate-pose renderer.')
(out/'pipeline-capture-tests.json').write_text(json.dumps(report,indent=2));print({k:v for k,v in report.items() if k!='samples'})
