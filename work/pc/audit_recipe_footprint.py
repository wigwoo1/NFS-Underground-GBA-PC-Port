"""Assess physical planes for exact retained writer coverage; no core/GPU draw."""
from pathlib import Path
import ctypes as C,json,hashlib,struct,zlib,collections
import numpy as np
here=Path(__file__).resolve().parent;base=Path(r'C:\NFSUG-Workspace');out=base/'NFSUG-pc-recipe-footprint-tests';out.mkdir(exist_ok=True)
# Reuse the receipt-checked owned archive decoder; stop before selection/GPU work.
original=here/'test_actual_recipe_gpu.py';prefix=original.read_text().split('# Choose actual visible geometries deterministically')[0];scope={'__file__':str(original),'__name__':'recipe_archive_reader'};exec(compile(prefix,str(original),'exec'),scope)
records=scope['records'];g=scope['g'];geodecode=scope['geodecode'];geofree=scope['geofree'];geobuffer=scope['geobuffer'];make=scope['blocks'];inside=scope['inside'];P=scope['P'];S=scope['S'];Q=scope['Q'];U=scope['U'];D=scope['D'];sha=scope['sha']
roadmap={};wallcalls={r['identity']:r for r in records if r['kind']==2}
for r in records:
 if r['kind']==1:
  first,count=struct.unpack_from('<2Q',r['blocks'][14],32)
  for ordinal in range(first,first+count):roadmap[ordinal]=r
wallmap={};raw=(base/'NFSUG-pc-wall-lineage-tests/wall-source-lineage.wclz').read_bytes();at=8
while at<len(raw):
 n=struct.unpack_from('<I',raw,at)[0];at+=4;blob=zlib.decompress(raw[at:at+n]);at+=n;pos=0
 while pos<len(blob):
  tag,n,epoch,refresh,call=struct.unpack_from('<5Q',blob,pos)
  if tag==3:wallmap[struct.unpack_from('<Q',blob,pos+40)[0]]=wallcalls[call]
  pos+=n
coverage=base/'NFSUG-pc-recipe-coverage-tests';receipt=json.loads((coverage/'coverage-test-report.json').read_text())
with __import__('os').add_dll_directory('C:/msys64/mingw64/bin'):lib=C.CDLL(str(coverage/'recipe-coverage.dll'))
f=scope['fn'](lib,'nf_pc_recipe_coverage_decode',[P,S,P,S,P,U,U,U,S],P);fr=scope['fn'](lib,'nf_pc_recipe_coverage_free',[P],None);get=scope['fn'](lib,'nf_pc_recipe_coverage_buffer',[P,U,P,P])
rows=[];cells=0;cache={};maximum_plane_distance=maximum_roundtrip=0.;outside=behind=parallel=nonplanar=0
for name,digest in receipt['fixture_sha256'].items():
 p=coverage/name;assert sha(p)==digest;raw=zlib.decompress(p.read_bytes()[8:]);fields=struct.unpack_from('<5Q4I',raw);key=(Q*5)(*fields[:5]);kind,top,bottom,hn=fields[5:];history=raw[56:56+hn];proof=raw[56+hn:];h=f(history,len(history),proof,len(proof),key,kind,top,bottom,64*1024*1024);assert h
 ptr=P();n=S();assert get(h,2,C.byref(ptr),C.byref(n));data=np.frombuffer(C.string_at(ptr,n.value),'<u8').reshape(-1,6).copy();fr(h)
 for ordinal in sorted(set(map(int,data[:,3]))):
  r=(roadmap if kind==2 else wallmap)[ordinal];identity=(r['kind'],r['identity'])
  if identity not in cache:
   keep,bs=make(r['blocks'][:12]);obj=geodecode(r['epoch'],r['refresh'],r['kind'],bs,12,65536);assert obj;ptr=P();n=S();assert geobuffer(obj,0,C.byref(ptr),C.byref(n));world=np.frombuffer(C.string_at(ptr,n.value),'<f8').reshape(-1,3).copy();geofree(obj)
   centroid=world.mean(axis=0);_,singular,basis=np.linalg.svd(world-centroid,full_matrices=False);normal=basis[-1];deviation=float(np.max(np.abs((world-centroid)@normal)));matrix=np.array(struct.unpack('<12i',r['blocks'][4 if kind==2 else 3]),float);R=np.array([[matrix[0],0,matrix[6]],[0,16384,0],[matrix[2],0,matrix[8]]])/16384;translation=matrix[9:12];cache[identity]=(world,centroid,basis,normal,deviation,R,translation)
  world,centroid,basis,normal,deviation,R,t=cache[identity];maximum_plane_distance=max(maximum_plane_distance,deviation);subset=data[data[:,3]==ordinal];xy=np.column_stack([subset[:,0]%240+.5,subset[:,0]//240+.5]);rays=np.column_stack([(xy[:,0]-120)/128,(xy[:,1]-87)/128,np.ones(len(xy))]);directions=rays@np.linalg.inv(R).T;den=directions@normal;valid=np.abs(den)>1e-12;parallel+=int(np.count_nonzero(~valid));depth=np.full(len(xy),np.nan);depth[valid]=np.dot(centroid+t,normal)/den[valid];positions=-t+directions[valid]*depth[valid,None];projected=(positions+t)@R.T;roundtrip=np.column_stack([120+128*projected[:,0]/projected[:,2],87+128*projected[:,1]/projected[:,2]]);error=float(np.max(np.abs(roundtrip-xy[valid]))) if valid.any() else 0.;maximum_roundtrip=max(maximum_roundtrip,error);local=(positions-centroid)@basis[:2].T;polygon=(world-centroid)@basis[:2].T;contained=inside(local,polygon);bad=int(np.count_nonzero(~contained));outside+=bad;back=int(np.count_nonzero(depth[valid]<64));behind+=back;nonplanar+=int(deviation>1e-6);cells+=len(subset);rows.append(dict(kind=kind-1,ordinal=ordinal,source_identity=r['identity'],source_refresh=r['refresh'],cells=len(subset),plane_max_distance=deviation,source_depth_min=float(np.nanmin(depth)),source_depth_max=float(np.nanmax(depth)),outside_physical_polygon=bad,below_near64=back,parallel=int(np.count_nonzero(~valid)),source_reprojection_error=error))
r=dict(result='AUDITED_EXACT_WRITER_PHYSICAL_PLANE_LIFT',cases=len(rows),cells=cells,unique_source_geometries=len(cache),maximum_plane_distance=maximum_plane_distance,nonplanar_writer_cases=nonplanar,parallel_rays=parallel,source_depth_below64_cells=behind,cells_outside_physical_polygon=outside,maximum_source_reprojection_error=maximum_roundtrip,coverage_receipt_sha256=sha(coverage/'coverage-test-report.json'),source_archive_reader_sha256=sha(original),executed_archive_prefix_sha256=hashlib.sha256(prefix.encode()).hexdigest(),script_sha256=sha(Path(__file__)),rows=rows,scope='Continuous raw Q14 matrix plane-ray intersection of original retained pixel centers. Source roundtrip algebra alone is not original quantized pixel/UV equivalence or complete world coverage.',core_opened=False,gpu_drawn=False,full_scene_60fps=False)
(out/'footprint-audit-report.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k!='rows'},indent=2))
