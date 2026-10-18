from pathlib import Path
import subprocess,json,struct,numpy as np
p=Path('work/camera').resolve();reports=[]
sources=[(frame,p/f'obj-gpu-{frame}.bin') for frame in (0,179,499,719)]
# A transparent higher priority semi-transparent OBJ changes retained color
# metadata. Ordinary alpha-discard sprite quads cannot reproduce this case.
row=bytearray(100480);struct.pack_into('<H',row,8,0x1044)
struct.pack_into('<H',row,8+0x50,0x400);struct.pack_into('<H',row,8+0x52,0x808)
for i in range(128):struct.pack_into('<H',row,99456+i*8,0x200)
struct.pack_into('<3H',row,99456,32,32,512|(3<<10))
struct.pack_into('<3H',row,99456+8,32|0x400,32,514)
row[128+0x14000:128+0x14020]=bytes([0x11])*32
struct.pack_into('<H',row,98432+512+2,31)
source=p/'obj-candidate-overlap.bin';source.write_bytes(row);sources.append(('overlap',source))
for frame,source in sources:
    target=p/f'obj-candidate-{frame}.rgba';ref=p/f'obj-candidate-{frame}-cpu.rgba'
    log=subprocess.check_output([str(p/'obj-candidate-gpu.exe'),str(source),str(target),str(ref)],text=True)
    actual=np.fromfile(target,np.uint32).reshape(2160,3840)[::-1]&0xffffff
    expected=np.fromfile(ref,np.uint32).reshape(2160,3840)&0xffffff
    diff=actual!=expected
    assert not diff.any(),(frame,int(diff.sum()),np.argwhere(diff)[:8].tolist())
    if frame=='overlap':
        # Inside both OBJ boxes: original red retained, higher semi flag halves
        # against native world even though the higher asset is transparent.
        x,y=740,440;yy=2159-y
        bg=(x&255)|((yy&255)<<8)|(((x//16+yy//16)&255)<<16)
        mixed=((255+(bg&255))//2)|((((bg>>8)&255)//2)<<8)|((((bg>>16)&255)//2)<<16)
        assert int(actual[y,x])==mixed,(int(actual[y,x]),mixed)
    reports.append(dict(sample=frame+1 if isinstance(frame,int) else frame,checked_pixels=3840*2160,gpu=log.strip()))
r=dict(result='PASS',samples=reports,scope='Captured HUD candidate color/metadata composed over independent native GPU gradient; CPU resolves OAM overlap and baked affine assets; no live integration, windows, or brightness preprocessing')
(p/'obj-candidate-gpu-tests.json').write_text(json.dumps(r,indent=2));print(r)
