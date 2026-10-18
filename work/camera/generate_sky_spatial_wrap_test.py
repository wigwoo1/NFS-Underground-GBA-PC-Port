from pathlib import Path
p=Path('work/camera');s=(p/'test_sky_continuous_gpu_readback.py').read_text().replace('import ctypes as C,struct,os,json','import ctypes as C,struct,os,json,math')
s=s.replace('owned-sky-gpu.dll','owned-sky-spatial-diagnostic.dll').replace('sky-continuous-gpu-readback-20261006','sky-spatial-wraps-20261007')
s=s.replace('error=max(abs(a-b) for a,b in zip(pixels[at:at+3],reference[i*4:i*4+3]));maximum=max(maximum,error)', '''px=int(300+(x+.5)*13.5);fraction=(px+.5-300)/13.5-x
    index=(samples.upper if fraction>=1-samples.weight else samples.lower)[i]
    color=struct.unpack_from('<H',palettes,y*512+index*2)[0]
    expected=tuple(((color>>k)&31)*8+(((color>>k)&31)>>2) for k in (0,5,10))
    error=max(abs(a-b) for a,b in zip(pixels[at:at+3],expected));maximum=max(maximum,error)''')
s=s.replace("'test_sky_continuous_gpu_readback.py','owned_sky_sampler.py'","'test_sky_spatial_wraps.py','owned_sky_sampler.py'")
s=s.replace('palettecolors within1unit. Background-only diagnostic','nearest spatial palette oracle within1unit. Background-only diagnostic')
(p/'test_sky_spatial_wraps.py').write_text(s)
