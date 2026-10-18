import ctypes as C,json,random,hashlib
from pathlib import Path
from project_paths import load_session
p=Path('work/camera');session=load_session(p/'prototype-runs/threaded-prepared-59aee71d90ee4c88a494da1a6b97ea61-session.json');rom=Path(session['rom']);protected=hashlib.sha256(rom.read_bytes()).hexdigest();size=rom.stat().st_size
d=C.CDLL(str((p/'visibility-probe-wide.dll').resolve()));d.nf_init.argtypes=[C.c_char_p,C.c_char_p];d.nf_capture_memory_read.argtypes=[C.c_uint,C.c_void_p,C.c_size_t];d.nf_capture_rom_copy_stats.argtypes=[C.c_void_p]
crt=C.CDLL('msvcrt');crt._putenv_s.argtypes=[C.c_char_p,C.c_char_p]
def flag(enabled):
 assert crt._putenv_s(b'NF_TEST_DIRECT_CAPTURE_ROM',b'1' if enabled else b'')==0
 assert crt._putenv_s(b'NF_TEST_VERIFY_CAPTURE_ROM',b'1' if enabled else b'')==0
flag(False);assert d.nf_init(session['rom'].encode(),b'')
rng=random.Random(601);ranges=[(0x08000000,1),(0x08000000+size-1,1),(0x08000000+size-4,4),(0x08000000+size-2,4),(0x0a000000,16),(0x0c000000,16),(0x07ffffff,2),(0xffffffff,2),(0x08000000,0)]
ranges += [(0x08000000+rng.randrange(size-1024),rng.randrange(1,1025)) for _ in range(256)]
copied=0;checks=0
try:
 for address,n in ranges:
  a=C.create_string_buffer(max(1,n));b=C.create_string_buffer(max(1,n));flag(False);ra=d.nf_capture_memory_read(address,a,n);stats=(C.c_uint64*3)();d.nf_capture_rom_copy_stats(stats);before=list(stats)
  flag(True);rb=d.nf_capture_memory_read(address,b,n);d.nf_capture_rom_copy_stats(stats);after=list(stats);assert ra==rb and (not ra or a.raw[:n]==b.raw[:n]),(hex(address),n)
  canonical=address>=0x08000000 and address+n<=min(0x0a000000,0x08000000+size)
  expected=n if ra and canonical else 0;assert after[0]-before[0]==expected;assert after[1]-before[1]==expected;assert after[2]==0;copied+=expected;checks+=1
finally:flag(False);d.nf_close()
assert hashlib.sha256(rom.read_bytes()).hexdigest()==protected
out=dict(result='PASS',boundary_and_random_cases=checks,verified_canonical_bytes=copied,zero_mismatches=True,rom_unchanged=True,scope='Canonical copy and mirror/out-of-image/overflow fallback parity; not full-scene live rendering or timing')
(p/'direct-rom-boundary-tests.json').write_text(json.dumps(out,indent=2));print(out)
