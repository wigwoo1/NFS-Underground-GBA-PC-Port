"""Alternating identical-input extraction comparison, not a gameplay benchmark."""
from pathlib import Path
import ctypes as C,struct,json,time,statistics,hashlib
p=Path('work/camera');R=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_void_p,C.c_size_t)
context=bytearray(44);struct.pack_into('<I',context,12,0x2000);struct.pack_into('<4I',context,16,0,0,512,512)
rect=struct.pack('<4i',0,0,240,160);bounds=struct.pack('<4H',0,240,0,160)
blocks={}
@R
def read(user,address,out,size):
    value=blocks.get(address)
    if value is None or len(value)<size:return 0
    C.memmove(out,value,size);return 1
dlls={}
for name,file in [('lookup','visibility-probe-wide.dll'),('reference','visibility-probe-wide-reference-palette.dll')]:
    d=C.CDLL(str((p/file).resolve()));d.nf_extract_billboard.argtypes=[R,C.c_void_p,C.c_uint32,C.c_uint32,C.c_void_p,C.c_void_p]
    d.nf_surface_free.argtypes=[C.c_void_p];dlls[name]=d
def extract(name):
    d=dlls[name];out=C.c_void_p();size=C.c_size_t();start=time.perf_counter_ns()
    assert d.nf_extract_billboard(read,None,0x1000,0x3000,C.byref(out),C.byref(size))
    elapsed=time.perf_counter_ns()-start
    try: return C.string_at(out,size.value),elapsed
    finally:d.nf_surface_free(out)
records=[]
for shift,height in ((3,4),(6,64),(9,512)):
    width=1<<shift;struct.pack_into('<HHI',context,36,shift,height,0x4000)
    blocks.update({0x1000:bytes(context),0x2000:rect,0x30e2:bounds,0x4000:bytes((i*37+11)&255 for i in range(width*height))})
    samples={name:[] for name in dlls};matched=0
    for trial in range(44):
        # Palette changes every trial; no persistent palette reuse is allowed.
        blocks[0x05000000]=b''.join(struct.pack('<H',(index*113+trial*157)&65535) for index in range(256))
        order=('lookup','reference') if trial%2==0 else ('reference','lookup')
        results={name:extract(name) for name in order}
        assert results['lookup'][0]==results['reference'][0]
        if trial>=4:
            matched+=1
            for name in dlls:samples[name].append(results[name][1]/1e6)
    stats={name:dict(median_ms=statistics.median(values),p95_ms=sorted(values)[int(.95*len(values))]) for name,values in samples.items()}
    records.append(dict(texels=width*height,exact_cases=matched,timings=stats,lookup_over_reference_median=stats['lookup']['median_ms']/stats['reference']['median_ms']))
report=dict(result='PASS',records=records,dll_sha256={name:hashlib.sha256((p/file).read_bytes()).hexdigest() for name,file in [('lookup','visibility-probe-wide.dll'),('reference','visibility-probe-wide-reference-palette.dll')]},
            scope='Alternating same-process synthetic billboard extraction, same compiler/settings and changing palettes; complete owned outputs identical. Includes read callbacks/allocation. Component comparison, not full-route pacing, model/road speed, input latency, original raster fidelity or smooth60fps proof.')
(p/'palette-lookup-benchmark-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
