"""Actual owned recipe surfaces, isolated from visibility/full-scene composition."""
from pathlib import Path
import ctypes as C,os,json,hashlib,struct,zlib,collections
import numpy as np
from PIL import Image
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-recipe-gpu-tests';geo=base/'NFSUG-pc-recipe-mesh-tests';roads=base/'NFSUG-pc-road-recipe-tests';walls=base/'NFSUG-pc-wall-lineage-tests'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
build=json.loads((out/'recipe-gpu-build-report.json').read_text());gb=json.loads((geo/'mesh-build-report.json').read_text());assert sha(out/'recipe-gpu.dll')==build['dll_sha256'] and sha(geo/'recipe-mesh.dll')==gb['dll_sha256']
for p,h in gb['source_sha256'].items():assert sha(p)==h
rr=json.loads((roads/'recipe-test-report.json').read_text());wr=json.loads((walls/'lineage-test-report.json').read_text());assert sha(roads/'road-source-recipes.nrrz')==rr['archive_sha256'] and sha(walls/'wall-source-lineage.wclz')==wr['archive_sha256']
with os.add_dll_directory('C:/msys64/mingw64/bin'):g=C.CDLL(str(geo/'recipe-mesh.dll'));d=C.CDLL(str(out/'recipe-gpu.dll'))
P=C.c_void_p;S=C.c_size_t;U=C.c_uint;Q=C.c_uint64;D=C.c_double
class Block(C.Structure):_fields_=[('data',P),('bytes',S)]
def fn(lib,n,args,res=C.c_int):f=getattr(lib,n);f.argtypes=args;f.restype=res;return f
geodecode=fn(g,'nf_pc_recipe_geometry_decode',[Q,U,U,P,U,S],P);geofree=fn(g,'nf_pc_recipe_geometry_free',[P],None);project=fn(g,'nf_pc_recipe_geometry_project',[P,P,P,P,P,D,P,P,S,P,S,P]);geobuffer=fn(g,'nf_pc_recipe_geometry_buffer',[P,U,P,P]);mesh=fn(d,'nf_pc_recipe_mesh_ring',[P,U,S],P);mf=fn(d,'nf_pc_recipe_mesh_free',[P],None);vertices=fn(d,'nf_pc_recipe_mesh_vertices',[P,P,P]);plane=fn(d,'nf_pc_recipe_mesh_plane',[P,U,P]);mat=fn(d,'nf_pc_recipe_material_decode',[U,P,U,S],P);mtf=fn(d,'nf_pc_recipe_material_free',[P],None);op=fn(d,'nf_pc_scene_gpu_open',[],P);close=fn(d,'nf_pc_scene_gpu_close',[P],None);error=fn(d,'nf_pc_scene_gpu_error',[],C.c_char_p);renderer=fn(d,'nf_pc_scene_gpu_renderer',[P],C.c_char_p);seed=fn(d,'nf_pc_scene_gpu_draw_sky',[P,P,S,P,S,D,P,S,U,U,U,U,U,U,P,S]);submit=fn(d,'nf_pc_scene_gpu_render_recipe',[P,P,P,P,S,U,U,P]);read=fn(d,'nf_pc_scene_gpu_read_target',[P,P,S])
pair=json.loads((geo/'camera-pair.json').read_text());A=(Q*5)(*pair['older']);B=(Q*5)(*pair['newer']);CA=(D*7)(*pair['older_pose']);CB=(D*7)(*pair['newer_pose']);proj=(D*3)(*pair['projection']);table=(roads/'source-reciprocals.bin').read_bytes()
def blocks(values):buf=[C.create_string_buffer(v) for v in values];return buf,(Block*len(buf))(*[Block(C.cast(v,P),len(values[i])) for i,v in enumerate(buf)])
def ring_for(record,alpha):
 keep,bs=blocks(record['blocks'][:12]);h=geodecode(record['epoch'],record['refresh'],record['kind'],bs,12,65536);assert h
 try:
  ring=(D*384)();n=U();assert project(h,A,CA,B,CB,alpha,proj,table,len(table),ring,C.sizeof(ring),C.byref(n));return np.array(ring[:n.value*6]).reshape(-1,6)
 finally:geofree(h)
def inside(points,polygon):
 result=np.zeros(len(points),bool)
 for i,b in enumerate(polygon):
  a=polygon[i-1];dy=b[1]-a[1]
  if dy:result^=((a[1]>points[:,1])!=(b[1]>points[:,1]))&(points[:,0]<(b[0]-a[0])*(points[:,1]-a[1])/dy+a[0])
 return result
records=[];raw=(roads/'road-source-recipes.nrrz').read_bytes();at=8
while at<len(raw):
 n=struct.unpack_from('<I',raw,at)[0];at+=4;rec=zlib.decompress(raw[at:at+n]);at+=n;head=struct.unpack_from('<10Q',rec);pos=80+head[5]*68;values=[]
 for i in range(12):n=struct.unpack_from('<I',rec,pos)[0];pos+=4;values.append(rec[pos:pos+n]);pos+=n
 n=struct.unpack_from('<I',rec,pos)[0];pos+=4;values += [rec[pos:pos+n],rec[80:80+head[5]*68],rec[:80]];records.append(dict(kind=1,epoch=head[2],refresh=head[3],identity=head[4],blocks=values))
raw=(walls/'wall-source-lineage.wclz').read_bytes();at=8;calls={};wall_sources=empty_wall_calls=0
while at<len(raw):
 n=struct.unpack_from('<I',raw,at)[0];at+=4;blob=zlib.decompress(raw[at:at+n]);at+=n;pos=0
 while pos<len(blob):
  tag,n,epoch,refresh,call=struct.unpack_from('<5Q',blob,pos);rec=blob[pos:pos+n]
  if tag==2:
   wall_sources+=1;values=[];cursor=64
   for j in range(12):size=struct.unpack_from('<I',rec,cursor)[0];cursor+=4;values.append(rec[cursor:cursor+size]);cursor+=size
   calls[call]=dict(kind=2,epoch=epoch,refresh=refresh,identity=call,blocks=values,header=rec[:64],writer=None)
  elif tag==3:
   item=calls[call]
   if item['writer'] is None or (len(rec)>160 and len(item['writer'])==160):item['writer']=rec
  elif tag==4:
   item=calls.pop(call);writer=item.pop('writer');header=item.pop('header')
   if writer is not None:item['blocks'] += [writer[80:160],writer[160:] or b'\0',header];records.append(item)
   else:empty_wall_calls+=1
  pos+=n
assert not calls and wall_sources==1553 and len(records)==1973-empty_wall_calls,(len(calls),wall_sources,len(records),empty_wall_calls)
# Choose actual visible geometries deterministically by independent grid coverage.
yy,xx=np.indices((41,61));points=np.column_stack([(xx.ravel()+.5)*240/61,(yy.ravel()+.5)*160/41]);groups=collections.defaultdict(list)
for item in records:
 if item['epoch']!=A[0] or item['refresh']>A[3]:continue
 ring=ring_for(item,.5)
 if len(ring)<3:continue
 clip=struct.unpack('<4H',item['blocks'][5]);mask=inside(points,ring[:,:2])&(points[:,0]>=clip[0])&(points[:,0]<clip[1])&(points[:,1]>=clip[2])&(points[:,1]<clip[3]);score=int(mask.sum())
 if score<8:continue
 group='road' if item['kind']==1 else 'wall_shaded' if len(item['blocks'][13])==4081 else 'wall_unshaded';item['score']=score;item['clip']=clip;item['category']=group;item['ring_mid']=ring;groups[group].append(item)
selected=[]
for category in ['road','wall_shaded','wall_unshaded']:
 pool=sorted(groups[category],key=lambda r:(-r['score'],r['refresh'],r['identity']));used=set()
 for item in pool:
  # Distinct owned source coordinate/material bytes, not cross-frame screen matching.
  signature=hashlib.sha256(item['blocks'][0]+item['blocks'][1]+item['blocks'][3 if item['kind']==1 else 4]).digest()
  if signature in used:continue
  used.add(signature);selected.append(item)
  if len(used)==2:break
 assert len(used)==2,(category,len(pool))
print('selected',[(x['category'],x['refresh'],x['identity'],x['score']) for x in selected],flush=True)

def palette(item):
 raw=np.frombuffer(item['blocks'][8 if item['kind']==1 else 9],dtype='<u2');rgb=np.array([((raw>>(c*5))&31) for c in range(3)]).T;rgba=np.column_stack([(rgb<<3)|(rgb>>2),np.full(256,255)]).astype(np.uint8);return np.broadcast_to(rgba,(160,256,4)).copy()
def indices(item):
 m=item['blocks'][3 if item['kind']==1 else 4];shift,stored=struct.unpack_from('<2H',m,36);w=1<<shift;h=stored//2 if item['kind']==1 else stored;raw=item['blocks'][7 if item['kind']==1 else 8]
 if item['kind']==1:src=np.frombuffer(raw,np.uint8,count=w*stored).reshape(h,w*2)[:,:w];return src,np.ones((h,w),bool)
 src=np.frombuffer(raw,np.uint8,count=w*h).reshape(h,w);idx=np.frombuffer(item['blocks'][13],np.uint8)[src.astype(np.uint32)*16] if len(item['blocks'][13])==4081 else src;return idx,src!=0

gpu=op();assert gpu,error();gpu_name=renderer(gpu).decode();rows=[];total_checked=total_ambiguous=total_boundary_diff=total_changed=total_preserved=0;zero=bytes(15136);seedpal=np.full((160,256,4),[211,29,197,255],np.uint8).tobytes()
try:
 for item in selected:
  keep,bs=blocks(item['blocks']);mh=mat(item['kind'],bs,15,64*1024*1024);assert mh;idx,write=indices(item);th,tw=idx.shape;pal=palette(item);pb=pal.tobytes();digests=[]
  try:
   for alpha in [0.,.5,1.]:
    ring=ring_for(item,alpha);raw=(D*ring.size)(*ring.ravel());meshh=mesh(raw,len(ring),65536);assert meshh;p=P();n=S();assert vertices(meshh,C.byref(p),C.byref(n));v=np.frombuffer(C.string_at(p,n.value),'<f4').reshape(-1,3,5).astype(float)
    try:
     for w,h,aw,ah in [(240,160,240,160),(3840,2160,3240,2160)]:
      output=C.create_string_buffer(w*h*4);assert seed(gpu,zero,15136,zero,15136,0,seedpal,len(seedpal),w,h,aw,ah,0,160,output,len(output)),error();before=np.frombuffer(output.raw,np.uint8).reshape(h,w,4).copy();expected=before.copy();uncertain=np.zeros((h,w),bool);coverage=np.zeros((h,w),bool);xx=(np.arange(aw)+.5)*240/aw;yy=(ah-np.arange(ah)-.5)*160/ah;clip=item['clip'];count=0
      for ti,tri in enumerate(v):
       xy=tri[:,:2];low=np.maximum([0,0],np.floor([xy[:,0].min()*aw/240-1,(160-xy[:,1].max())*ah/160-1])).astype(int);high=np.minimum([aw,ah],np.ceil([xy[:,0].max()*aw/240+1,(160-xy[:,1].min())*ah/160+1])).astype(int);lx,ly=low;rx,ry=high
       if lx>=rx or ly>=ry:continue
       x=xx[lx:rx][None,:];y=yy[ly:ry,None];a,b,c=xy;det=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);assert det
       beta=((x-a[0])*(c[1]-a[1])-(y-a[1])*(c[0]-a[0]))/det;gamma=((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]))/det;weights=[1-beta-gamma,beta,gamma];inside_tri=(weights[0]>=0)&(beta>=0)&(gamma>=0);band=(x>=clip[0])&(x<clip[1])&(y>=clip[2])&(y<clip[3]);covered=inside_tri&band;coverage[ly:ry,lx:rx]|=covered
       for ei in range(3):
        u=xy[ei];z=xy[(ei+1)%3];px=x*aw/240;py=y*ah/160;ux,uy=u*[aw/240,ah/160];zx,zy=z*[aw/240,ah/160];distance=np.abs((zx-ux)*(py-uy)-(zy-uy)*(px-ux))/np.hypot(zx-ux,zy-uy);uncertain[ly:ry,lx:rx]|=(distance<=1/128)&band
       uvq=sum(weights[j][:,:,None]*tri[j,2:] for j in range(3));q=uvq[:,:,2];safe=np.where(q!=0,q,1);uv=uvq[:,:,:2]/safe[:,:,None]
       # Error bound around texel boundaries includes exported plane quantization
       # and float shader arithmetic; oracle itself uses independent barycentrics.
       coeff=(C.c_float*11)();assert plane(meshh,ti,coeff);co=np.array(coeff,float);dx=x-co[0];dy=y-co[1];terms=co[2:5]+dx[:,:,None]*co[5:8]+dy[:,:,None]*co[8:11];den=np.where(terms[:,:,2]!=0,terms[:,:,2],1);shaderuv=terms[:,:,:2]/den[:,:,None];magnitude=np.abs(co[2:5])+np.abs(dx[:,:,None]*co[5:8])+np.abs(dy[:,:,None]*co[8:11]);err=16*np.finfo(np.float32).eps*magnitude;bound=np.abs(shaderuv-uv)+(err[:,:,:2]+np.abs(shaderuv)*err[:,:,2,None])/np.maximum(np.abs(den[:,:,None])-err[:,:,2,None],1e-30)
       dims=np.array([tw,th]);scaled=uv*dims;near=(np.abs(scaled-np.rint(scaled))<=bound*dims+1e-7).any(axis=2);uncertain[ly:ry,lx:rx]|=covered&near
       tx=np.floor((uv[:,:,0]%1)*tw).astype(np.int64)%tw;ty=np.floor((uv[:,:,1]%1)*th).astype(np.int64)%th;ink=covered&write[ty,tx];iy,ix=np.nonzero(ink);source_rows=(((ah-(iy+ly))*2-1)*80)//ah;expected[iy+ly,ix+lx,:3]=pal[source_rows,idx[ty[iy,ix],tx[iy,ix]],:3];expected[iy+ly,ix+lx,3]=255;count+=int(ink.sum())
      assert submit(gpu,meshh,mh,pb,len(pb),aw,ah,(U*4)(*clip)),error();assert read(gpu,output,len(output)),error();actual=np.frombuffer(output.raw,np.uint8).reshape(h,w,4);diff=np.any(actual!=expected,axis=2);bad=diff&~uncertain;assert not bad.any(),(item['category'],item['identity'],alpha,w,int(bad.sum()),np.argwhere(bad)[:5].tolist())
      outside=~coverage&~uncertain;assert np.array_equal(actual[outside],before[outside]);changed=int(np.count_nonzero(np.any(actual!=before,axis=2)));total_changed+=changed;total_checked+=w*h-int(uncertain.sum());total_ambiguous+=int(uncertain.sum());total_boundary_diff+=int((diff&uncertain).sum());total_preserved+=int(outside.sum());digest=hashlib.sha256(output.raw).hexdigest();digests.append((alpha,w,digest));rows.append(dict(category=item['category'],refresh=item['refresh'],identity=item['identity'],alpha=alpha,size=[w,h,aw,ah],clip=clip,triangles=len(v),drawn_pixels=count,changed_pixels=changed,uncertain_pixels=int(uncertain.sum()),differences_in_uncertain_region=int((diff&uncertain).sum()),sha256=digest))
      if alpha==.5 and w==3840:Image.fromarray(actual[::-1].copy()).save(out/(item['category']+'-'+str(item['identity'])+'-isolated-4k.png'))
      print('PASS',item['category'],item['identity'],alpha,w,'changed',changed,'ambiguous',int(uncertain.sum()),flush=True)
    finally:mf(meshh)
   # Explicitly record image motion; transparent or clipped surfaces may not move visibly.
   item['image_motion']={str(w):len({h for a,width,h in digests if width==w}) for w in [240,3840]}
  finally:mtf(mh)
finally:close(gpu)
r=dict(result='PASS_ACTUAL_OWNED_RECIPE_GPU_COMPONENT',renderer=gpu_name,cases=len(rows),selected_surfaces=len(selected),wall_source_calls=wall_sources,wall_calls_without_accepted_writer=empty_wall_calls,candidate_groups={k:len(v) for k,v in groups.items()},pixels_compared_away_from_boundaries=total_checked,uncertain_pixels=total_ambiguous,differences_in_uncertain_regions=total_boundary_diff,pixel_differences_outside_declared_boundaries=0,pixels_outside_surface_preserved=total_preserved,changed_pixels=total_changed,rows=rows,selected=[{k:v for k,v in item.items() if k not in ['blocks','ring_mid']} for item in selected],dll_sha256=sha(out/'recipe-gpu.dll'),build_report_sha256=sha(out/'recipe-gpu-build-report.json'),geometry_dll_sha256=sha(geo/'recipe-mesh.dll'),camera_pair_sha256=sha(geo/'camera-pair.json'),road_archive_sha256=rr['archive_sha256'],wall_archive_sha256=wr['archive_sha256'],script_sha256=sha(Path(__file__)),scope='Actual isolated historical surfaces at three camera poses, raw source palette repeated across rows and actual source clip bounds; independent barycentric pixel oracle with declared edge/texel ambiguity. Original per-writer effective shade only; not true full-wall lighting or retained writer coverage. No core opened.',live_host_integration=False,full_scene_60fps=False)
(out/'actual-recipe-gpu-test-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['rows','selected']},indent=2))
