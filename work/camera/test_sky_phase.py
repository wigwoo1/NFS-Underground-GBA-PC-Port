import argparse,ctypes as C,hashlib,json,math,struct
from pathlib import Path
from dataclasses import replace
from owned_sky_boundary import SkyBoundary
from owned_sky_sampler import SkyAsset
p=argparse.ArgumentParser();p.add_argument("--dll",required=True);p.add_argument("--records",required=True);p.add_argument("--rom",required=True);p.add_argument("--output",required=True);a=p.parse_args()
class Boundary(C.Structure):_fields_=[("epoch",C.c_uint64),("refresh",C.c_uint32),("angle",C.c_uint32),("source",C.c_uint32),("origin",C.c_uint32),("destination",C.c_uint32),("center",C.c_int32),("indices",C.c_void_p)]
class Sample(C.Structure):_fields_=[("lower",C.c_void_p),("upper",C.c_void_p),("phase",C.c_double),("weight",C.c_double),("lower_offset",C.c_uint),("upper_offset",C.c_uint),("exact",C.c_uint)]
d=C.CDLL(a.dll);d.nf_sky_boundary_decode.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(Boundary)]
d.nf_sky_phase_sample.argtypes=[C.POINTER(Boundary),C.POINTER(Boundary),C.c_void_p,C.c_size_t,C.c_double,C.c_uint,C.POINTER(Sample)]
rom=Path(a.rom).read_bytes();records=[]
for r in json.loads(Path(a.records).read_text())["sky_boundaries"]:
 start=r["source"]-0x08000000;data=rom[start:start+15136]
 assert hashlib.sha256(data).hexdigest()==r["source_sha256"]
 records.append(SkyBoundary(r["epoch"],r["copy_refresh"],r["angle"],240,64,0,r["source"],r["asset_origin"],r["destination"],data))
def native(b):
 owner=C.create_string_buffer(b.encode());out=Boundary()
 assert d.nf_sky_boundary_decode(owner,len(b.encode()),C.byref(out));return owner,out
tests=0
for old,new in zip(records,records[1:]):
 if old.asset_origin!=new.asset_origin:continue
 asset=SkyAsset(old.asset_origin,rom[old.asset_origin-0x08000000:old.asset_origin-0x08000000+15376]);buffer=C.create_string_buffer(asset.data)
 oa,na=native(old);ob,nb=native(new)
 for mode in (0,1):
  for alpha in (0,.125,.25,.5,.75,.875,1):
   out=Sample();assert d.nf_sky_phase_sample(C.byref(na),C.byref(nb),buffer,15376,alpha,mode,C.byref(out))
   expected=asset.sample_continuous(old,new,alpha) if mode else asset.sample(old,new,alpha)
   assert abs(out.weight-expected.weight)<1e-10
   assert C.string_at(out.lower,15136)==expected.lower and C.string_at(out.upper,15136)==expected.upper
   tests+=1
# Synthetic wrap boundaries, same immutable ROM source. Each endpoint still
# verifies the exact original integer copy; only the phase is synthetic.
asset=SkyAsset(records[0].asset_origin,rom[records[0].asset_origin-0x08000000:records[0].asset_origin-0x08000000+15376])
from owned_sky_scroll import source_offset
for angles in [(4090,4104),(4104,4090),(16380,8),(8,16380)]:
 pair=[]
 for index,angle in enumerate(angles):
  off=source_offset(angle,240,0);pair.append(replace(records[0],refresh=100+index,angle=angle,source=asset.origin+off,indices=asset.data[off:off+15136]))
 old,new=pair;oa,na=native(old);ob,nb=native(new);buffer=C.create_string_buffer(asset.data)
 phases=[]
 for alpha in [i/32 for i in range(33)]:
  out=Sample();assert d.nf_sky_phase_sample(C.byref(na),C.byref(nb),buffer,15376,alpha,1,C.byref(out))
  expected=asset.sample_continuous(old,new,alpha)
  assert abs(out.weight-expected.weight)<1e-10 and C.string_at(out.lower,15136)==expected.lower
  phases.append(out.phase);tests+=1
 assert max(abs((y-x+120)%240-120) for x,y in zip(phases,phases[1:]))<1
# Invalid calls do not change their output.
negative=0
for which in ["epoch","asset","reverse","nan","alpha","mode","ambiguous"]:
 oa,na=native(records[0]);ob,nb=native(records[1]);data=bytearray(rom[na.origin-0x08000000:na.origin-0x08000000+15376])
 alpha=.5;mode=1
 if which=="epoch":nb.epoch+=1
 elif which=="asset":data[na.source-na.origin]^=255
 elif which=="reverse":nb.refresh=na.refresh-1
 elif which=="nan":alpha=float("nan")
 elif which=="alpha":alpha=1.1
 elif which=="mode":mode=2
 else:
  # Keep a valid ROM copy but make the angle interval ambiguous.
  b=records[1];angle=(records[0].angle+2048)&16383;off=source_offset(angle,240,0);_,nb=native(replace(b,angle=angle,source=b.asset_origin+off,indices=bytes(data[off:off+15136])))
 buffer=C.create_string_buffer(bytes(data));out=Sample();C.memset(C.byref(out),0x55,C.sizeof(out));before=bytes(out)
 assert not d.nf_sky_phase_sample(C.byref(na),C.byref(nb),buffer,15376,alpha,mode,C.byref(out)) and bytes(out)==before,which
 negative+=1
report=dict(result="PASS",native_reference_samples=tests,wrap_pairs=4,invalid_atomic_cases=negative,scope="Native phase/owned-source sampler parity with independent Python implementation; not GPU or gameplay verification")
Path(a.output).write_text(json.dumps(report,indent=2));print(report)
