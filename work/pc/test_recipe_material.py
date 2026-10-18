from pathlib import Path
import os,ctypes as C,json,hashlib,struct,zlib,collections
import numpy as np
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-recipe-mesh-tests'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((out/'mesh-build-report.json').read_text());assert sha(out/'recipe-mesh.dll')==build['dll_sha256']
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'recipe-mesh.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint
class Block(C.Structure):_fields_=[('data',P),('bytes',S)]
def fn(name,args,result=C.c_int):f=getattr(d,name);f.argtypes=args;f.restype=result;return f
op=fn('nf_pc_recipe_material_decode',[U,P,U,S],P);close=fn('nf_pc_recipe_material_free',[P],None);info=fn('nf_pc_recipe_material_info',[P,P]);buffer=fn('nf_pc_recipe_material_buffer',[P,U,P,P])
def make(values):b=[C.create_string_buffer(v) for v in values];return b,(Block*len(b))(*[Block(C.cast(v,P),len(values[i])) for i,v in enumerate(b)])
def get(m,i):p=P();n=S();assert buffer(m,i,C.byref(p),C.byref(n));return C.string_at(p,n.value)
road_dir=base/'NFSUG-pc-road-recipe-tests';wall_dir=base/'NFSUG-pc-wall-lineage-tests';rr=json.loads((road_dir/'recipe-test-report.json').read_text());wr=json.loads((wall_dir/'lineage-test-report.json').read_text());assert sha(road_dir/'road-source-recipes.nrrz')==rr['archive_sha256'] and sha(wall_dir/'wall-source-lineage.wclz')==wr['archive_sha256'];seen=set();bindings=collections.Counter();decoded=texels=opaque_zero=skipped=shaded_texels=0;held_blocks=None;guards=0

def check(kind,blocks,synthetic=False):
 global decoded,texels,opaque_zero,skipped,shaded_texels,held_blocks,guards
 mat=blocks[3 if kind==1 else 4];shift,stored=struct.unpack_from('<2H',mat,36);width=1<<shift;height=stored//2 if kind==1 else stored;texture=blocks[7 if kind==1 else 8];shaded=kind==2 and len(blocks[13])==4081
 key=(kind,width,height,hashlib.sha256(texture).digest(),hashlib.sha256(blocks[13]).digest() if shaded else None)
 bindings[kind]+=not synthetic
 if key in seen:return
 seen.add(key);buffers,a=make(blocks);m=op(kind,a,15,64*1024*1024);assert m;meta=(Q*5)();assert info(m,meta) and tuple(meta[:4])==(kind,width,height,shaded)
 if kind==1:source=np.frombuffer(texture,dtype=np.uint8,count=width*stored).reshape(height,width*2)[:,:width].copy();index=source.copy();state=np.where(index==0,1,2).astype(np.uint8)
 else:
  source=np.frombuffer(texture,dtype=np.uint8,count=width*height).reshape(height,width);index=source.copy()
  if shaded:index=np.frombuffer(blocks[13],dtype=np.uint8)[source.astype(np.uint32)*16];index=np.where(source==0,0,index).astype(np.uint8)
  state=np.where(source==0,0,np.where(index==0,1,2)).astype(np.uint8)
 rgba=np.zeros((height,width,4),dtype=np.uint8);rgba[:,:,0]=index;rgba[:,:,3]=np.where(state,255,0);assert get(m,0)==index.tobytes() and get(m,1)==state.tobytes() and get(m,2)==rgba.tobytes()
 decoded+=1;texels+=width*height;opaque_zero+=int(np.count_nonzero(state==1));skipped+=int(np.count_nonzero(state==0));shaded_texels+=width*height if shaded else 0
 if guards==0:
  assert not op(kind,a,15,meta[4]-1);exact=op(kind,a,15,meta[4]);assert exact;close(exact);assert not op(3,a,15,64*1024*1024);p=P(123);n=S(456);assert not buffer(m,3,C.byref(p),C.byref(n)) and (p.value,n.value)==(123,456);guards+=3
  for v in buffers:C.memset(v,0,len(v))
  assert get(m,2)==rgba.tobytes();guards+=1
 close(m)
raw=(road_dir/'road-source-recipes.nrrz').read_bytes();at=8
while at<len(raw):
 n=struct.unpack_from('<I',raw,at)[0];at+=4;record=zlib.decompress(raw[at:at+n]);at+=n;header=struct.unpack_from('<10Q',record);pos=80+header[5]*68;blocks=[]
 for i in range(12):n=struct.unpack_from('<I',record,pos)[0];pos+=4;blocks.append(record[pos:pos+n]);pos+=n
 n=struct.unpack_from('<I',record,pos)[0];pos+=4;blocks+=[record[pos:pos+n],record[80:80+header[5]*68],record[:80]];check(1,blocks)
raw=(wall_dir/'wall-source-lineage.wclz').read_bytes();at=8;calls={}
while at<len(raw):
 n=struct.unpack_from('<I',raw,at)[0];at+=4;blob=zlib.decompress(raw[at:at+n]);at+=n;pos=0
 while pos<len(blob):
  tag,size,epoch,refresh,call=struct.unpack_from('<5Q',blob,pos);record=blob[pos:pos+size]
  if tag==2:
   p=64;blocks=[]
   for i in range(12):n=struct.unpack_from('<I',record,p)[0];p+=4;blocks.append(record[p:p+n]);p+=n
   calls[call]=(blocks,record[:64])
  elif tag==3:
   blocks,meta=calls[call];values=blocks+[record[80:160],record[160:] or b'\0',meta];check(2,values)
   if held_blocks is None:held_blocks=values
  elif tag==4:calls.pop(call)
  pos+=size
assert not calls and bindings=={1:420,2:27027}
# Explicit source0 skip vs nonzero->mapped0 write, including maximum index255.
blocks=list(held_blocks);texture=bytearray(blocks[8]);texture[:3]=bytes([0,1,255]);blocks[8]=bytes(texture);lookup=bytearray(b'\x58'*4081);lookup[0]=99;lookup[16]=0;lookup[4080]=17;blocks[13]=bytes(lookup);check(2,blocks,True);buffers,a=make(blocks);m=op(2,a,15,64*1024*1024);assert m and get(m,0)[:3]==bytes([0,0,17]) and get(m,1)[:3]==bytes([0,1,2]);close(m)
short=list(blocks);short[13]=short[13][:-1];buffers,a=make(short);assert not op(2,a,15,64*1024*1024);guards+=1
r=dict(result='PASS_OWNED_ORIGINAL_WRITER_INDEXED_MATERIALS',road_recipe_bindings=bindings[1],wall_writer_bindings=bindings[2],unique_material_cases=decoded,texels_compared=texels,shaded_texels_compared=shaded_texels,opaque_index_zero_texels=opaque_zero,transparent_wall_source_zero_texels=skipped,source_zero_and_mapped_zero_distinguished=True,maximum_source_index255_checked=True,negative_budget_buffer_and_lookup_checks=guards,input_lifetime_owned=True,dll_sha256=sha(out/'recipe-mesh.dll'),build_report_sha256=sha(out/'mesh-build-report.json'),script_sha256=sha(Path(__file__)),road_archive_sha256=rr['archive_sha256'],wall_archive_sha256=wr['archive_sha256'],scope='Original per-writer effective remap. Does not regenerate lighting across an entire sampled wall or establish visibility/coverage.',gpu_verified=False,full_scene_60fps=False)
(out/'material-test-report.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
