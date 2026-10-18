from pathlib import Path
import ctypes as C,random,struct,subprocess,json,numpy as np
p=Path('work/camera').resolve();d=C.CDLL(str(p/'obj-tile.dll'));f=d.nf_obj_bg_backdrop_pixel;f.argtypes=[C.c_uint32]*8;f.restype=C.c_uint32;rng=random.Random(681);rows=[]
def color():
 c=rng.randrange(32768);return 0xff000000|sum(((((c>>j)&31)<<3)|(((c>>j)&31)>>2))<<k for j,k in ((0,0),(5,8),(10,16)))
for n in range(1024):rows.append((color() if n&1 else 0,rng.randrange(4)|(rng.randrange(2)<<2),color() if n&2 else 0,rng.randrange(4),color(),rng.randrange(64)|(rng.randrange(4)<<6)|(rng.randrange(64)<<8),rng.randrange(32)|(rng.randrange(32)<<8),rng.randrange(32)))
source=p/'obj-effect-gpu-input.bin';source.write_bytes(b''.join(struct.pack('<8I',*r) for r in rows));target=p/'obj-effect-gpu.rgba';log=subprocess.check_output([str(p/'obj-effect-gpu.exe'),str(source),str(target)],text=True);actual=np.fromfile(target,dtype=np.uint32).reshape(2160,3840)[::-1]&0xffffff;expected=np.zeros((2160,3840),np.uint32)
for i,r in enumerate(rows):
 value=f(*r)&0xffffff;x=(i%60)*64;y=(i//60)*120;expected[y:y+120,x:x+64]=value
 if not np.all(actual[y:y+120,x:x+64]==value):raise AssertionError((i,hex(value),hex(int(actual[y,x])),r))
assert np.array_equal(actual,expected)
combinations={(bool(r[0]),bool(r[2]),(r[1]>>2)&3,(r[5]>>6)&3) for r in rows};assert len(combinations)==32
r=dict(input_combinations=32,result='PASS',cases=1024,checked_target_pixels=3840*2160,scope='GPU OBJ/BG2/backdrop priority, alpha/brighten/darken/color targets vs verified native CPU component; constant candidate inputs, no live HUD texture/window/scene integration',gpu=log.strip());(p/'obj-effect-gpu-tests.json').write_text(json.dumps(r,indent=2));print(r)
