from pathlib import Path
from project_paths import load_session
import ctypes as C,json,hashlib
p=Path(__file__).resolve().parent;session=load_session(p/'prototype-runs/threaded-prepared-59aee71d90ee4c88a494da1a6b97ea61-session.json');rom=Path(session['rom']);before=hashlib.sha256(rom.read_bytes()).hexdigest();data=rom.read_bytes()
d=C.CDLL(str(p/'visibility-probe-wide.dll'));d.nf_init.argtypes=[C.c_char_p]*2;f=d.nf_capture_memory_read;f.argtypes=[C.c_uint32,C.c_void_p,C.c_size_t];d.nf_read.argtypes=[C.c_uint,C.c_int];crt=C.CDLL('msvcrt');crt._putenv_s.argtypes=[C.c_char_p]*2
assert d.nf_init(str(rom).encode(),b'')
try:
 for flag in ('NF_TEST_DIRECT_CAPTURE_ROM','NF_TEST_VERIFY_CAPTURE_ROM'):assert crt._putenv_s(flag.encode(),b'1')==0
 cases=[(0x08000000,1),(0x080000c4,8),(0x08010001,4096),(0x08000000+len(data)-4096,4096),(0x08000000+len(data)-1,1)]
 for address,size in cases:
  out=C.create_string_buffer(size);assert f(address,out,size);expected=bytes(d.nf_read(address+i,1) for i in range(size));assert out.raw==expected==data[address-0x08000000:address-0x08000000+size]
 bad=[(0x08000000+len(data)-1,2),(0x0a000000,16),(0x0c000000,16),(0xfffffff0,32),(0x08000000,0x100000)]
 for address,size in bad:
  out=C.create_string_buffer(b'X'*32,32);assert not f(address,out,size) and out.raw==b'X'*32
 out=C.create_string_buffer(b'Y'*16,16);assert not f(0x08000000,None,16) and out.raw==b'Y'*16
 stats=(C.c_uint64*3)();d.nf_capture_rom_copy_stats.argtypes=[C.c_void_p];d.nf_capture_rom_copy_stats(stats);assert stats[0]==stats[1]==sum(n for _,n in cases) and stats[2]==0
finally:d.nf_close()
assert hashlib.sha256(rom.read_bytes()).hexdigest()==before
report=dict(result='PASS_ROM_CAPTURE_BOUNDARIES',accepted_cases=len(cases),rejected_atomic_cases=len(bad),verified_bytes=stats[1],rom_unchanged=True,scope='Canonical image copy boundaries; existing capture policy rejects mirrors/oversize/outofimage. No live60fps proof.')
(p/'rom-capture-boundary-tests.json').write_text(json.dumps(report,indent=2));print(report)
