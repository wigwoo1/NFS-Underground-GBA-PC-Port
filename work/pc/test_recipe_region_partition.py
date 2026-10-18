from pathlib import Path
import ctypes as C,os,json,struct,hashlib
here=Path(__file__).resolve().parent;out=Path(r'C:\NFSUG-Workspace\NFSUG-pc-recipe-region-tests')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
b=json.loads((out/'region-build-report.json').read_text());assert sha(out/'recipe-regions.dll')==b['dll_sha256']
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'recipe-regions.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint
f=d.nf_pc_recipe_coverage_decode;f.argtypes=[P,S,P,S,P,U,U,U,S];f.restype=P;cf=d.nf_pc_recipe_coverage_free;cf.argtypes=[P];cf.restype=None;create=d.nf_pc_recipe_regions_create;create.argtypes=[P,S];create.restype=P;free=d.nf_pc_recipe_regions_free;free.argtypes=[P];free.restype=None;buf=d.nf_pc_recipe_regions_buffer;buf.argtypes=[P,P,P];info=d.nf_pc_recipe_regions_info;info.argtypes=[P,P]
def run(name,events,owned,expected):
 asset=struct.pack('<8Q',1,80,1,1,0x08000000,16,0,0)+bytes([11,22])*8;records=[]
 for ordinal,start,width,duplicate in events:
  command=[0]*17;command[5]=0x08000000;command[6]=0x06000000+start;command[7]=width;command[16]=duplicate;records.append(struct.pack('<12Q',2,164,ordinal,7,1,0,0x08000000,1,0,0,0,0)+struct.pack('<17I',*command))
 payload=asset+b''.join(records);history=struct.pack('<8Q',0x3148524e,1,64+len(payload),9,1,len(events),0,0)+payload;proof=bytearray(192080);struct.pack_into('<10Q',proof,0,0x3150524e,1,192080,9,1,0,7,8,0,38400)
 for cell in owned:proof[80+cell]=1;struct.pack_into('<I',proof,38480+cell*4,7)
 key=(Q*5)(9,1,0,7,0);coverage=f(history,len(history),bytes(proof),len(proof),key,2,0,160,64*1024*1024);assert coverage,name;r=create(coverage,64*1024*1024);assert r,name;cf(coverage)
 try:
  p=P();n=S();assert buf(r,C.byref(p),C.byref(n));raw=C.string_at(p,n.value);actual=[struct.unpack_from('<8Q',raw,at) for at in range(0,len(raw),64)];assert actual==expected,(name,actual,expected);meta=(Q*9)();assert info(r,meta) and meta[6]==len(owned) and meta[7]==len(expected)
 finally:free(r)
 return dict(name=name,cells=len(owned),rectangles=len(expected))
rows=[]
rows.append(run('row-end-wrap',[(123,238,3,0)],list(range(238,244)),[(9,1,123,7,238,240,0,1),(9,1,123,7,0,4,1,2)]))
rows.append(run('vertical-duplicate-merge',[(123,32,2,1)],list(range(32,36))+list(range(272,276)),[(9,1,123,7,32,36,0,2)]))
rows.append(run('retained-hole',[(123,10,3,0)],[10,11,14,15],[(9,1,123,7,10,12,0,1),(9,1,123,7,14,16,0,1)]))
rows.append(run('adjacent-writers',[(123,10,1,0),(124,12,1,0)],[10,11,12,13],[(9,1,123,7,10,12,0,1),(9,1,124,7,12,14,0,1)]))
rows.append(run('empty-proof-selected-layer',[(123,10,3,0)],[],[]))
r=dict(result='PASS_COVERAGE_REGION_PARTITION_BOUNDARIES',cases=len(rows),rows=rows,dll_sha256=sha(out/'recipe-regions.dll'),build_report_sha256=sha(out/'region-build-report.json'),script_sha256=sha(Path(__file__)),core_opened=False,full_scene_60fps=False)
(out/'region-partition-test-report.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
