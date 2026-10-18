from pathlib import Path
import ctypes as C,json,random
p=Path(__file__).resolve().parent;d=C.CDLL(str(p/'visibility-probe-wide.dll'));crt=C.CDLL('msvcrt');crt._putenv_s.argtypes=[C.c_char_p,C.c_char_p];assert crt._putenv_s(b'NF_TEST_WALL_SHADE_LOOKUP_CACHE',b'1')==0
f=d.nf_wall_shade_lookup;f.argtypes=[C.c_void_p]*3;stats=d.nf_wall_shade_lookup_stats;stats.argtypes=[C.c_void_p]
r=random.Random(780);palette=bytearray(r.randbytes(512));table=bytearray(r.randbytes(4096));out=(C.c_ubyte*16384)()
def reference():
 result=bytearray()
 for level in range(16):
  for index in range(256):
   at=table[index*16+level]*2;color=palette[at]|palette[at+1]<<8
   result.extend(((color&31)*255//31,((color>>5)&31)*255//31,((color>>10)&31)*255//31,255 if index else 0))
 return bytes(result)
def check():
 a=(C.c_ubyte*512).from_buffer_copy(palette);b=(C.c_ubyte*4096).from_buffer_copy(table)
 assert f(a,b,out);assert bytes(out)==reference()
check();check()
for i in range(128):
 block=palette if i%2 else table;at=r.randrange(len(block));block[at]^=1<<r.randrange(8);check();check()
s=(C.c_uint64*2)();stats(s);assert s[0]==129 and s[1]==129
sentinel=bytes(out);assert not f(None,None,out) and bytes(out)==sentinel
report=dict(result='PASS_EXACT_SHADE_LOOKUP',mutated_inputs=128,cache_hits=s[0],cache_misses=s[1],independent_rgba_arithmetic=True,null_output_atomic=True,scope='Palette/table lookup component; full lighting texture and live60fps remain unverified')
(p/'wall-shade-lookup-tests.json').write_text(json.dumps(report,indent=2));print(report)
