from pathlib import Path
import os,ctypes as C,json,hashlib,zlib,struct,collections,threading
import numpy as np
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-recipe-writer-tests';road=base/'NFSUG-pc-road-recipe-tests';wall=base/'NFSUG-pc-wall-lineage-tests';coverage=base/'NFSUG-pc-recipe-coverage-tests'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
build=json.loads((out/'writer-build-report.json').read_text());assert sha(out/'recipe-writer.dll')==build['dll_sha256']
for p,h in build['source_sha256'].items():assert sha(p)==h
rr=json.loads((road/'recipe-test-report.json').read_text());wr=json.loads((wall/'lineage-test-report.json').read_text());cr=json.loads((coverage/'coverage-test-report.json').read_text());assert sha(road/'road-source-recipes.nrrz')==rr['archive_sha256'] and sha(wall/'wall-source-lineage.wclz')==wr['archive_sha256']
recipes={};raw=(road/'road-source-recipes.nrrz').read_bytes();at=8
while at<len(raw):
 n=struct.unpack_from('<I',raw,at)[0];at+=4;rec=zlib.decompress(raw[at:at+n]);at+=n;head=struct.unpack_from('<10Q',rec);pos=80+head[5]*68;values=[]
 for i in range(12):n=struct.unpack_from('<I',rec,pos)[0];pos+=4;values.append(rec[pos:pos+n]);pos+=n
 n=struct.unpack_from('<I',rec,pos)[0];pos+=4;values=tuple(values+[rec[pos:pos+n],rec[80:80+head[5]*68],rec[:80]])
 for ordinal in range(head[4],head[4]+head[5]):recipes[(1,ordinal)]=(values,head[3])
raw=(wall/'wall-source-lineage.wclz').read_bytes();at=8;calls={}
while at<len(raw):
 n=struct.unpack_from('<I',raw,at)[0];at+=4;data=zlib.decompress(raw[at:at+n]);at+=n;pos=0
 while pos<len(data):
  tag,n,epoch,refresh,call=struct.unpack_from('<5Q',data,pos);rec=data[pos:pos+n]
  if tag==2:
   cursor=64;values=[]
   for i in range(12):size=struct.unpack_from('<I',rec,cursor)[0];cursor+=4;values.append(rec[cursor:cursor+size]);cursor+=size
   calls[call]=(tuple(values),rec[:64])
  elif tag==3:
   values,header=calls[call];ordinal=struct.unpack_from('<Q',rec,40)[0];recipes[(2,ordinal)]=(values+(rec[80:160],rec[160:] or b'\0',header),refresh)
  elif tag==4:calls.pop(call)
  pos+=n
assert not calls and len(recipes)==74241
with os.add_dll_directory('C:/msys64/mingw64/bin'):d=C.CDLL(str(out/'recipe-writer.dll'));c=C.CDLL(str(coverage/'recipe-coverage.dll'))
P=C.c_void_p;S=C.c_size_t;Q=C.c_uint64;U=C.c_uint
class Block(C.Structure):_fields_=[('data',P),('bytes',S)]
def fn(lib,n,args,res=C.c_int):f=getattr(lib,n);f.argtypes=args;f.restype=res;return f
op=fn(d,'nf_pc_recipe_writer_decode',[P,U,Q,U,P,U,S],P);free=fn(d,'nf_pc_recipe_writer_free',[P],None);info=fn(d,'nf_pc_recipe_writer_info',[P,P]);buffer=fn(d,'nf_pc_recipe_writer_buffer',[P,U,P,P]);sample=fn(d,'nf_pc_recipe_writer_cell',[P,U,U,P]);decode=fn(c,'nf_pc_recipe_coverage_decode',[P,S,P,S,P,U,U,U,S],P);cf=fn(c,'nf_pc_recipe_coverage_free',[P],None);cb=fn(c,'nf_pc_recipe_coverage_buffer',[P,U,P,P])
def make(values):keep=[C.create_string_buffer(v) for v in values];return keep,(Block*15)(*[Block(C.cast(v,P),len(values[i])) for i,v in enumerate(keep)])
def blob(f,*args):p=P();n=S();assert f(*args,C.byref(p),C.byref(n));return C.string_at(p,n.value) if n.value else b''
writer_cases=cells=opaque_zero=source_zero_written=shaded=guards=0;by_kind=collections.Counter();rows=[];held=None;tested_kinds=set();max_timing_gap=0
for name,h in cr['fixture_sha256'].items():
 path=coverage/name;assert sha(path)==h;raw=zlib.decompress(path.read_bytes()[8:]);fields=struct.unpack_from('<5Q4I',raw);key=(Q*5)(*fields[:5]);kind,top,bottom,hn=fields[5:];history=raw[56:56+hn];proof=raw[56+hn:];view=decode(history,len(history),proof,len(proof),key,kind,top,bottom,64*1024*1024);assert view;records=np.frombuffer(blob(cb,view,2),'<u8').reshape(-1,6).copy();cf(view)
 for ordinal in sorted(set(map(int,records[:,3]))):
  rkind=kind-1;values,write=recipes[(rkind,ordinal)];selected=records[records[:,3]==ordinal];assert (selected[:,4]==write).all();keep,blocks=make(values);w=op(key,rkind,ordinal,write,blocks,15,64*1024*1024);assert w,(list(key),rkind,ordinal,write);meta=(Q*10)();assert info(w,meta) and list(meta[:7])==list(key)+[rkind,ordinal] and meta[8]==write;max_timing_gap=max(max_timing_gap,write-meta[7]);texture=values[7 if rkind==1 else 8];palette=values[8 if rkind==1 else 9];shade=values[13] if rkind==2 else b'\0';assert blob(buffer,w,1)==texture and blob(buffer,w,2)==shade and blob(buffer,w,3)==palette and blob(buffer,w,4)==values[3 if rkind==1 else 4]
  for v in keep:C.memset(v,0,len(v))
  for row in selected:
   cell=int(row[0]);result=(Q*4)();assert sample(w,cell%240,cell//240,result);offset,src,index,state=map(int,result);assert state==(2 if row[5] else 1) and index==row[5] and offset<len(texture) and src==texture[offset],('Writer sample mismatch',rkind,ordinal,cell,list(result),int(row[5]));expected=shade[src*16] if rkind==2 and len(shade)==4081 else src;assert index==expected and (rkind==1 or src!=0);cells+=1;by_kind[rkind]+=1;opaque_zero+=state==1;source_zero_written+=src==0;shaded+=rkind==2 and len(shade)==4081
  if rkind not in tested_kinds:
   tested_kinds.add(rkind);keep,blocks=make(values);assert not op(key,rkind,ordinal,write,blocks,15,meta[9]-1);exact=op(key,rkind,ordinal,write,blocks,15,meta[9]);assert exact;free(exact);guards+=1
   bad=(Q*5)(*key);bad[0]+=1;assert not op(bad,rkind,ordinal,write,blocks,15,64*1024*1024);guards+=1
   sentinel=(Q*4)(123,456,789,999)
   for x,y in [(240,0),(0,160)]:assert not sample(w,x,y,sentinel) and list(sentinel)==[123,456,789,999];guards+=1
   p=P(123);n=S(456);assert not buffer(w,5,C.byref(p),C.byref(n)) and (p.value,n.value)==(123,456);guards+=1
   if rkind==2:
    short=list(values);short[13]=bytes(4080);keep,blocks=make(short);assert not op(key,rkind,ordinal,write,blocks,15,64*1024*1024);guards+=1
  if held is None:held=(w,tuple(map(int,selected[0])),tuple(blob(buffer,w,i) for i in range(5)));w=None
  if w:free(w)
  writer_cases+=1
 rows.append(dict(owner=list(key),kind=kind,cells=len(records)))
worker_result=[]
def worker():
 w,row,buffers=held;assert tuple(blob(buffer,w,i) for i in range(5))==buffers;result=(Q*4)();assert sample(w,row[0]%240,row[0]//240,result) and result[2]==row[5];free(w);worker_result.append(True)
t=threading.Thread(target=worker);t.start();t.join();assert worker_result==[True]
assert cells==50494 and writer_cases==666
# Every archived accepted writer must decode, including currently invisible ones.
all_decoded=0;maximum_binding_bytes=0;all_capture_write_gap=0
for (kind,ordinal),(values,write) in recipes.items():
 epoch=struct.unpack_from('<Q',values[14],16)[0];owner=(Q*5)(epoch,1,0,write,0);keep,blocks=make(values);w=op(owner,kind,ordinal,write,blocks,15,64*1024*1024);assert w,('Archived writer decode rejected',kind,ordinal,write);meta=(Q*10)();assert info(w,meta);maximum_binding_bytes=max(maximum_binding_bytes,meta[9]);all_capture_write_gap=max(all_capture_write_gap,meta[8]-meta[7]);free(w);all_decoded+=1
assert all_decoded==74241
r=dict(result='PASS_OWNED_ORIGINAL_WRITER_TEXTURE_INDEX_BINDINGS',writer_cases=writer_cases,retained_cells=cells,cells_by_recipe_kind=dict(by_kind),opaque_mapped_zero_cells=opaque_zero,road_source_zero_opaque_cells=source_zero_written,shaded_wall_cells=shaded,maximum_capture_to_write_gap=max_timing_gap,canonical_recipe_keys_loaded=len(recipes),all_archived_writer_decodes=all_decoded,maximum_single_binding_bytes=maximum_binding_bytes,all_writer_maximum_capture_to_write_gap=all_capture_write_gap,raw_texture_shade_palette_material_and_command_owned=True,source_inputs_overwritten_before_sampling=True,worker_read_sample_free=True,negative_budget_owner_cell_buffer_shade_guards=guards,rows=rows,dll_sha256=sha(out/'recipe-writer.dll'),build_report_sha256=sha(out/'writer-build-report.json'),coverage_report_sha256=sha(coverage/'coverage-test-report.json'),road_archive_sha256=rr['archive_sha256'],wall_archive_sha256=wr['archive_sha256'],script_sha256=sha(Path(__file__)),scope='Exact original integer writer texture-index/address sampling at actual retained source-cell centers. Does not infer continuous authored UV, per-scanline display palette, GPU textures or full-scene order.',core_opened=False,gpu_drawn=False,full_scene_60fps=False)
(out/'writer-test-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='rows'},indent=2))
