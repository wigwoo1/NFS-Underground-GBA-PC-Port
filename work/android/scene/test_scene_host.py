"""Real native packet ownership checks; no scene rendering or gameplay claim."""
from pathlib import Path
import argparse,ctypes as C,json,hashlib,os,struct
a=argparse.ArgumentParser();a.add_argument("--library",type=Path,required=True);a.add_argument("--fixtures",type=Path,required=True);a.add_argument("--report",type=Path,required=True);a=a.parse_args()
class Sample(C.Structure):_fields_=[("epoch",C.c_uint64),("older",C.c_uint64),("newer",C.c_uint64),("alpha",C.c_double),("target",C.c_double)]
class Pair(C.Structure):_fields_=[("time",Sample),("older",C.c_void_p),("older_size",C.c_size_t),("newer",C.c_void_p),("newer_size",C.c_size_t)]
with os.add_dll_directory(r"C:\msys64\mingw64\bin"):
 d=C.CDLL(str(a.library))
 d.nf_android_scene_open.argtypes=[C.c_void_p,C.c_size_t];d.nf_android_scene_open.restype=C.c_void_p
 d.nf_android_scene_close.argtypes=[C.c_void_p]
 d.nf_android_scene_info.argtypes=[C.c_void_p,C.POINTER(C.c_uint64)]
 for name in ("nf_android_scene_copy","nf_android_scene_section"):getattr(d,name).restype=C.c_size_t
 d.nf_android_scene_copy.argtypes=[C.c_void_p,C.c_void_p,C.c_size_t]
 d.nf_android_scene_section.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_size_t]
 assert not d.nf_android_scene_open(None,256*1024*1024+1)
 sentinel=(C.c_uint64*12)(*[77]*12)
 assert not d.nf_android_scene_info(None,sentinel) and list(sentinel)==[77]*12
 rows=[];payloads=[];rejects=0
 for f in sorted(a.fixtures.glob("*.bin")):
  raw=f.read_bytes();head=struct.unpack_from("<8I",raw);assert head[0]==0x3150534e
  parts=[struct.unpack_from("<3I",raw,32+i*12) for i in range(5)]
  source=C.create_string_buffer(raw);h=d.nf_android_scene_open(source,len(raw));assert h,f
  try:
   C.memset(source,0,len(raw))
   info=(C.c_uint64*12)();assert d.nf_android_scene_info(h,info)
   model_magic,model_count=struct.unpack_from("<2I",raw,parts[0][1])
   expected_models=1 if model_magic==0x324d464e else model_count
   world=struct.unpack_from("<I",raw,parts[1][1]+4)[0]
   expected=[head[4],head[5],head[6],head[7],len(raw),expected_models,world]+[p[2] for p in parts]
   assert list(info)==expected,(list(info),expected)
   owned=C.create_string_buffer(len(raw))
   assert d.nf_android_scene_copy(h,owned,len(raw))==len(raw) and owned.raw==raw
   C.memset(owned,165,len(raw));assert d.nf_android_scene_copy(h,owned,len(raw)-1)==0 and owned.raw==b"\xa5"*len(raw)
   for i,(_,offset,size) in enumerate(parts):
    section=C.create_string_buffer(size)
    assert d.nf_android_scene_section(h,i,section,size)==size and section.raw==raw[offset:offset+size]
    C.memset(section,165,size)
    assert d.nf_android_scene_section(h,i,section,size-1)==0 and section.raw==b"\xa5"*size
   assert not d.nf_android_scene_section(h,5,owned,len(raw))
  finally:d.nf_android_scene_close(h)
  for length in (0,4,91,len(raw)-1):
   assert not d.nf_android_scene_open(raw,length);rejects+=1
  for offset in (0,8,12,36):
   bad=bytearray(raw);struct.pack_into("<I",bad,offset,0xffffffff)
   assert not d.nf_android_scene_open(bytes(bad),len(bad));rejects+=1
  rows.append({"file":f.name,"sha256":hashlib.sha256(raw).hexdigest(),"info":expected})
  payloads.append(raw)
 # Exercise the exact shared immutable snapshot store with real packet payloads.
 d.nf_snapshot_create.argtypes=[C.c_size_t];d.nf_snapshot_create.restype=C.c_void_p
 d.nf_snapshot_push.argtypes=[C.c_void_p,C.c_uint64,C.c_uint64,C.c_double,C.c_void_p,C.c_size_t]
 d.nf_snapshot_acquire.argtypes=[C.c_void_p,C.c_double,C.c_double,C.POINTER(Pair)]
 d.nf_snapshot_release.argtypes=[C.c_void_p];d.nf_snapshot_destroy.argtypes=[C.c_void_p]
 store=d.nf_snapshot_create(sum(map(len,payloads[:2])));assert store
 for i,raw in enumerate(payloads[:2]):assert d.nf_snapshot_push(store,5,i+1,i+1,raw,len(raw))
 pair=Pair();assert d.nf_snapshot_acquire(store,1.5,0,C.byref(pair))==2
 assert (pair.time.epoch,pair.time.older,pair.time.newer,pair.time.alpha)==(5,1,2,.5)
 assert C.string_at(pair.older,pair.older_size)==payloads[0] and C.string_at(pair.newer,pair.newer_size)==payloads[1]
 assert not d.nf_snapshot_push(store,6,3,0,payloads[0],len(payloads[0])) and not d.nf_snapshot_destroy(store)
 d.nf_snapshot_release(store)
 assert d.nf_snapshot_push(store,6,3,0,payloads[0],len(payloads[0]))
 assert not d.nf_snapshot_push(store,5,4,1,payloads[0],len(payloads[0]))
 sentinel=Pair();C.memset(C.byref(sentinel),77,C.sizeof(sentinel));before=bytes(sentinel)
 assert not d.nf_snapshot_acquire(store,float("nan"),0,C.byref(sentinel)) and bytes(sentinel)==before
 assert d.nf_snapshot_destroy(store)
 report={"result":"PASS_SHARED_SCENE_HOST","real_packets":rows,"malformed_cases_rejected":rejects,
 "input_poisoning_preserved_owned_bytes":True,"short_buffer_outputs_unchanged":True,
 "snapshot_pair_pinning_and_epoch_reset":True,"android_runtime":False,"gpu_rendering":False}
 a.report.write_text(json.dumps(report,indent=2))
 print(json.dumps({k:v for k,v in report.items() if k!="real_packets"},indent=2))
