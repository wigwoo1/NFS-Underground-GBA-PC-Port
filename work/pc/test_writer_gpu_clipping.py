from pathlib import Path
import ctypes as C,json,hashlib,struct,zlib,collections
import numpy as np
here=Path(__file__).resolve().parent;original=here/'test_region_mask_gpu.py';boot=original.read_text().split('try:\n for name,h in cr[')[0].replace('NFSUG-pc-region-mask-tests','NFSUG-pc-writer-gpu-tests');ns={'__file__':str(original),'__name__':'near_gpu_inputs'};exec(compile(boot,str(original),'exec'),ns)
# Reuse receipt-checked entry points, before any actual mask case executes.
P=ns['P'];S=ns['S'];Q=ns['Q'];U=ns['U'];D=ns['D'];base=ns['base'];out=ns['out'];gpu=ns['gpu'];d=ns['d'];archive=ns['archive'];env=ns['env'];make=ns['make'];blob=ns['blob'];matrix=env['matrix'];A=ns['A'];B=ns['B'];CA=ns['CA'];projection=ns['projection'];pa=env['pa'];ring=ns['ring'];mesh=ns['mesh'];mf=ns['mf'];fn=ns['fn'];sha=ns['sha'];rows=[];counts=collections.Counter();regions=f=writer=address=None
try:
 name=next(n for n in ns['cr']['fixture_sha256'] if n=='owner-146-2.nccz');p=base/'NFSUG-pc-recipe-coverage-tests'/name;assert sha(p)==ns['cr']['fixture_sha256'][name];raw=zlib.decompress(p.read_bytes()[8:]);fields=struct.unpack_from('<5Q4I',raw);key=(Q*5)(*fields[:5]);kind,top,bottom,hn=fields[5:];c=ns['cover'](raw[56:56+hn],hn,raw[56+hn:],192080,key,kind,top,bottom,64*1024*1024);assert c;regions=ns['create'](c,64*1024*1024);assert regions;ns['cf'](c);rects=np.frombuffer(blob(ns['rbuffer'],regions),'<u8').reshape(-1,8);ri=0;v=rects[ri];epoch,rkind,ordinal,refresh,l,r,t,bt=map(int,v);item=archive['roadmap'][ordinal];keep,bs=make(item['blocks'][:12]);geometry=ns['gd'](epoch,item['refresh'],rkind,bs,12,65536);assert geometry;f=ns['fc'](geometry,ordinal,refresh,projection,65536);assert f;ns['gf'](geometry)
 # Uniform raw texture over this actual source rectangle isolates clipping/address lookup.
 assert (r-l)%2==0 and bt-t in [1,2]
 Block=archive['scope']['Block'];values=[bytes(1)]*15;material=bytearray(48);struct.pack_into('<HHI',material,36,0,2,0x08000000);values[3]=bytes(material);values[7]=bytes([17])*16;values[8]=bytes(512);command=[0]*17;command[5]=0x08000000;command[6]=0x06000000+t*240+l;command[7]=(r-l)//2;command[16]=bt-t-1;values[13]=struct.pack('<17I',*command);values[14]=struct.pack('<10Q',0x3152524e,80,9,1,1,1,0,0,0,0);buffers=[C.create_string_buffer(v) for v in values];blocks=(Block*15)(*[Block(C.cast(v,P),len(values[i])) for i,v in enumerate(buffers)])
 writer=fn(d,'nf_pc_recipe_writer_decode',[P,U,Q,U,P,U,S],P)((Q*5)(9,1,0,2,0),1,1,1,blocks,15,64*1024*1024);assert writer;address=fn(d,'nf_pc_writer_address_map',[P,S],P)(writer,64*1024*1024);assert address
 draw_writer=fn(d,'nf_pc_scene_gpu_render_writer',[P,P,U,P,P,P,P,S,U,U,U,U])
 world,centroid,basis,normal,deviation,_,_=archive['cache'][(rkind,item['identity'])];xy=np.array([[l,t],[r,t],[r,bt],[l,bt]],float);rays=np.column_stack([(xy[:,0]-120)/128,(xy[:,1]-87)/128,np.ones(4)]);directions=rays@matrix(pa[3:]);depth=np.dot(centroid-pa[:3],normal)/(directions@normal);points=pa[:3]+directions*depth[:,None];q=np.array([.13,.27,.07,.95]);q/=np.linalg.norm(q);R=matrix(q);center=points.mean(axis=0);initial=(points-center)@R.T;z=sorted(initial[:,2]);assert min(np.diff(z))>1e-6;shifts=[z[0]-128]+[(z[i]+z[i+1])/2-64 for i in range(3)]+[z[-1]+128]
 for shift in shifts:
  position=center+np.array([0,0,shift])@R;visible=env['clip_project']((points-position)@R.T)
  if len(visible):
   shift_x=float(np.mean((visible[:,0]-120)*visible[:,2]/128));shift_y=float(np.mean((visible[:,1]-87)*visible[:,2]/128));position=center+np.array([shift_x,shift_y,shift])@R
  pose=(D*7)(*position,*q);output=(D*36)();n=U();assert ring(regions,ri,f,A,CA,B,pose,1.,projection,output,C.sizeof(output),C.byref(n));counts[str(n.value)]+=1;m=mesh(output,n.value,65536);assert m;triangles=np.frombuffer(blob(ns['vertices'],m),'<f4').reshape(-1,3,5).astype(float);mf(m)
  for w,h,aw,ah in [(240,160,240,160),(3840,2160,3240,2160)]:
   rawout=C.create_string_buffer(w*h*4);assert ns['seed'](gpu,ns['zero'],15136,ns['zero'],15136,0,ns['empty_palette'],163840,w,h,aw,ah,0,0,rawout,len(rawout));expected=np.zeros((h,w),bool);uncertain=np.zeros((h,w),bool);xx=(np.arange(aw)+.5)*240/aw;yy=(ah-np.arange(ah)-.5)*160/ah
   for tri in triangles:
    xy=tri[:,:2];lo=np.maximum([0,0],np.floor([xy[:,0].min()*aw/240-1,(160-xy[:,1].max())*ah/160-1])).astype(int);hi=np.minimum([aw,ah],np.ceil([xy[:,0].max()*aw/240+1,(160-xy[:,1].min())*ah/160+1])).astype(int);lx,ly=lo;rx,ry=hi
    if lx>=rx or ly>=ry:continue
    x=xx[lx:rx][None,:];y=yy[ly:ry,None];edges=[]
    for ei in range(3):
     a=xy[ei];b=xy[(ei+1)%3];cross=(b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]);edges.append(cross);length=np.hypot((b[0]-a[0])*aw/240,(b[1]-a[1])*ah/160);uncertain[ly:ry,lx:rx]|=np.abs(cross)*aw*ah/(240*160)/length<=1/128
    edges=np.array(edges);expected[ly:ry,lx:rx]|=(edges>=0).all(axis=0)|(edges<=0).all(axis=0)
   color=bytes([17,0,0,255]);assert draw_writer(gpu,output,n.value,(U*4)(l,r,t,bt),writer,address,ns['empty_palette'],163840,aw,ah,0,1),ns['error']();assert ns['read'](gpu,rawout,len(rawout));pixels=np.frombuffer(rawout.raw,np.uint8).reshape(h,w,4);actual=pixels[:,:,3]!=0;diff=actual!=expected;bad=diff&~uncertain;assert not bad.any(),('Near-mask leakage/loss',n.value,w,int(bad.sum()));assert np.all(pixels[actual]==np.array([17,0,0,255],np.uint8));rows.append(dict(vertices=n.value,size=[w,h,aw,ah],covered_pixels=int(actual.sum()),raster_boundary_pixels=int(uncertain.sum()),differences_within_boundary=int((diff&uncertain).sum()),differences_outside_boundary=int(bad.sum())))
 assert all(str(k) in counts for k in [0,3,4,5])
 for vertices in [3,4,5]:assert any(row['vertices']==vertices and row['size'][0]==3840 and row['covered_pixels']>0 for row in rows),('Clipping case must be visibly on screen',vertices)
 assert all(row['covered_pixels']==0 for row in rows if row['vertices']==0)
finally:
 if address:fn(d,'nf_pc_writer_address_map_free',[P],None)(address)
 if writer:fn(d,'nf_pc_recipe_writer_free',[P],None)(writer)
 if f:ns['ff'](f)
 if regions:ns['free'](regions)
 ns['close'](gpu);ns['mtf'](ns['material'])
r=dict(result='PASS_RAW_WRITER_GPU_NEAR_PLANE_CLIPPING',cases=len(rows),clip_vertex_counts=dict(counts),pixel_differences_outside_declared_raster_edges=0,rows=rows,gpu_dll_sha256=sha(out/'recipe-gpu.dll'),region_dll_sha256=sha(out/'recipe-regions.dll'),source_gpu_test_sha256=sha(original),executed_input_prefix_sha256=hashlib.sha256(boot.encode()).hexdigest(),script_sha256=sha(Path(__file__)),scope='Forced source region camera clipping, independent float-triangle mask oracle, 1/128 target-pixel edge region. Uniform raw source texture via original writer address descriptor, index-output mode; not a complete scene.',full_scene_60fps=False)
(out/'writer-near-gpu-test-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='rows'},indent=2))
