from pathlib import Path
import ctypes as C,os,json,zlib,struct,hashlib
import numpy as np
here=Path(__file__).resolve().parent;out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-recipe-coverage-tests')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
build=json.loads((out/'coverage-build-report.json').read_text());prior=json.loads((out/'coverage-test-report.json').read_text());assert sha(out/'recipe-coverage.dll')==build['dll_sha256']==prior['dll_sha256']
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'recipe-coverage.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint
f=d.nf_pc_recipe_coverage_decode;f.argtypes=[P,S,P,S,P,U,U,U,S];f.restype=P;free=d.nf_pc_recipe_coverage_free;free.argtypes=[P];free.restype=None;buf=d.nf_pc_recipe_coverage_buffer;buf.argtypes=[P,U,P,P]
def get(h,k):p=P();n=S();assert buf(h,k,C.byref(p),C.byref(n));return C.string_at(p,n.value)
cases=rows=guards=0
for name,h in prior['fixture_sha256'].items():
 path=out/name;assert sha(path)==h;raw=path.read_bytes();assert raw[:8]==b'NCCZ\x01\0\0\0';data=zlib.decompress(raw[8:]);fields=struct.unpack_from('<5Q4I',data);key=(Q*5)(*fields[:5]);kind,top,bottom,hn=fields[5:];history=data[56:56+hn];proof=data[56+hn:];assert len(proof)==192080
 original=f(history,len(history),proof,len(proof),key,kind,top,bottom,64*1024*1024);assert original
 try:
  rgba=get(original,0);source=get(original,1);writers=np.frombuffer(get(original,2),'<u8').reshape(-1,6).copy();modified=bytearray(history);pos=64;events=[]
  while pos<len(modified):
   tag,n=struct.unpack_from('<2Q',modified,pos)
   if tag==2:events.append(pos);ordinal=struct.unpack_from('<Q',modified,pos+16)[0];struct.pack_into('<Q',modified,pos+16,ordinal+(1<<40))
   pos+=n
  high=f(bytes(modified),len(modified),proof,len(proof),key,kind,top,bottom,64*1024*1024);assert high
  try:
   actual=np.frombuffer(get(high,2),'<u8').reshape(-1,6);writers[:,3]+=1<<40;assert np.array_equal(actual,writers) and get(high,0)==rgba and get(high,1)==source;rows+=len(writers);cases+=1
  finally:free(high)
  assert len(events)>1;bad=bytearray(history);a,b=events[:2];struct.pack_into('<Q',bad,b+16,struct.unpack_from('<Q',bad,a+16)[0]);assert not f(bytes(bad),len(bad),proof,len(proof),key,kind,top,bottom,64*1024*1024);guards+=1
  badproof=bytearray(proof);badproof[24]^=1;assert not f(history,len(history),bytes(badproof),len(badproof),key,kind,top,bottom,64*1024*1024);guards+=1
 finally:free(original)
r=dict(result='PASS_RETAINED_WRITER_64BIT_KEYS_AND_PROOF_GUARDS',cases=cases,rows_checked=rows,key_increment=1<<40,rgba_and_source_records_unchanged=True,duplicate_ordinal_and_wrong_proof_rejected=guards,dll_sha256=sha(out/'recipe-coverage.dll'),main_test_report_sha256=sha(out/'coverage-test-report.json'),script_sha256=sha(Path(__file__)),core_opened=False,full_scene_60fps=False)
(out/'coverage-key-test-report.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
