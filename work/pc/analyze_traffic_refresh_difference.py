"""Analyze saved source difference and compare actual native renderer inputs/output."""
from pathlib import Path
import argparse,ctypes as C,hashlib,json,os,struct
from source_frame_witness import capture_witness,function as fn,P,S,U,Q
base=Path(r'C:\NFSUG-Workspace');parser=argparse.ArgumentParser();parser.add_argument('--folder',type=Path,default=base/'NFSUG-pc-traffic-refresh-route-tests/first-source-difference');parser.add_argument('--scene-dll',type=Path,default=base/'NFSUG-pc-scene-tests/source-scene.dll');parser.add_argument('--write-images',action='store_true');args=parser.parse_args();folder=args.folder;scene_path=args.scene_dll;report=json.loads((folder/'difference-witness-report.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def tree(a,b,path,depth=0):
 assert len(a)==len(b),(path,len(a),len(b))
 offsets=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y];result=dict(path=path,bytes=len(a),differences=len(offsets),first_offsets=offsets[:24],first_values=[[i,a[i],b[i]] for i in offsets[:12]])
 if offsets and depth<4 and len(a)>=128:
  parts=[];end=128;valid=True
  for i in range(4):
   at,n=struct.unpack_from('<QQ',a,64+16*i);bt,bn=struct.unpack_from('<QQ',b,64+16*i)
   if (at,n)!=(bt,bn):valid=False;break
   if not n:continue
   if at!=end or at+n>len(a):valid=False;break
   parts.append((i,at,n));end=at+n
  if valid and parts and end==len(a):result['children']=[tree(a[:128],b[:128],path+'/header',5)]+[tree(a[at:at+n],b[at:at+n],path+f'/part{i}',depth+1) for i,at,n in parts]
 return result
raw=[]
for row in json.loads((folder/'baseline/witness-components.json').read_text()):
 name=row['file'];a=(folder/'baseline'/name).read_bytes();b=(folder/'candidate'/name).read_bytes();raw.append(tree(a,b,name))
dll_dirs=[os.add_dll_directory(str(p)) for p in [scene_path.parent,Path('C:/msys64/mingw64/bin')] if p.is_dir()];d=C.CDLL(str(scene_path))
provenance={}
aux=[]
for label in ['baseline','candidate']:
 data=(folder/label/'owner0-kind0.bin').read_bytes()
 for k in [0,0,3]:
  at,n=struct.unpack_from('<QQ',data,64+16*k);data=data[at:at+n]
 assert len(data)==5312;aux.append(data)
identity=json.loads((folder/'baseline/witness-components.json').read_text())[0]['owner_info']
records=[[list(struct.unpack_from('<8Q',data,64+i*64)) for i in range(2)] for data in aux]
selected=[[i for i,record in enumerate(rows) if record[:5]==identity] for rows in records]
assert selected[0]==selected[1] and len(selected[0])==1
unused=1-selected[0][0];at=64+unused*64
provenance=dict(selected_owner=identity,selected_record_index=selected[0][0],selected_record_exact=records[0][selected[0][0]]==records[1][selected[1][0]],unselected_record_index=unused,old_unselected_record=records[0][unused],new_unselected_record=records[1][unused],everything_except_unselected_record_exact=aux[0][:at]==aux[1][:at] and aux[0][at+64:]==aux[1][at+64:])
assert provenance['selected_record_exact'] and provenance['everything_except_unselected_record_exact']
frames=[];scenes=[];buffers=[];infos=[]
def view(name,args):
 pointer=P();size=S();ok=fn(d,name,[P]+[U]*(len(args)-1)+[P,P])(*args,C.byref(pointer),C.byref(size))
 return C.string_at(pointer,size.value) if ok else None
try:
 for label in ['baseline','candidate']:
  frame=capture_witness(d,folder/label,report['frame_info'][label]);frames.append(frame);scene=fn(d,'nf_pc_scene_prepare',[P,S],P)(frame,64*1024*1024);assert scene,label;scenes.append(scene);m=(Q*8)();assert fn(d,'nf_pc_scene_info',[P,P])(scene,m);infos.append(list(m));parts={}
  for k in range(2):parts[f'base{k}']=view('nf_pc_scene_buffer',[scene,k])
  for k in range(3):parts[f'hud{k}']=view('nf_pc_scene_hud_buffer',[scene,k])
  for owner in range(int(m[2])):
   for kind in [2,3]:
    for k in range(3):parts[f'retention{owner}/{kind}/{k}']=view('nf_pc_scene_retention_buffer',[scene,owner,kind,k])
  for command in range(int(m[3])):
   cm=(Q*16)();assert fn(d,'nf_pc_scene_command_info',[P,U,P])(scene,command,cm);parts[f'command{command}/info']=bytes(cm)
   for k in range(2):parts[f'command{command}/buffer{k}']=view('nf_pc_scene_command_buffer',[scene,command,k])
   for level in range(32 if cm[8] else 1):parts[f'command{command}/image{level}']=view('nf_pc_scene_command_image',[scene,command,level])
   columns=(U*3240)();ok=fn(d,'nf_pc_scene_command_columns',[P,U,U,P,S])(scene,command,3240,columns,C.sizeof(columns));parts[f'command{command}/columns']=bytes(columns) if ok else None
  buffers.append(parts)
 assert buffers[0].keys()==buffers[1].keys()
 changed=[k for k in buffers[0] if buffers[0][k]!=buffers[1][k]];gpu_results=[]
 gpu=fn(d,'nf_pc_scene_gpu_open',[],P)();assert gpu
 try:
  for w,h,aw in [(240,160,240),(3840,2160,3240)]:
   images=[]
   for label,scene in zip(['baseline','candidate'],scenes):
    pixels=C.create_string_buffer(w*h*4);assert fn(d,'nf_pc_scene_gpu_draw',[P,P,U,U,U,U,P,S])(gpu,scene,w,h,aw,h,pixels,len(pixels));data=pixels.raw;images.append(data)
    if args.write_images:(folder/f'{label}-{w}.rgba').write_bytes(data)
   gpu_results.append(dict(width=w,height=h,active_width=aw,equal=images[0]==images[1],different_pixels=sum(images[0][i:i+4]!=images[1][i:i+4] for i in range(0,len(images[0]),4)),sha256=[hashlib.sha256(x).hexdigest() for x in images]))
 finally:fn(d,'nf_pc_scene_gpu_close',[P],None)(gpu)
 result=dict(auxiliary_provenance=provenance,result='ANALYZED_FROZEN_TRAFFIC_REFRESH_SOURCE_DIFFERENCE',logic_step=report['logic_step'],raw_components=raw,prepared_scene_info=infos,prepared_buffers_compared=len(buffers[0]),changed_prepared_buffers=changed,prepared_bytes_compared=sum(len(v) for v in buffers[0].values() if v is not None),gpu=gpu_results,original_pixels_equal=(folder/'baseline/original-pixels.bin').read_bytes()==(folder/'candidate/original-pixels.bin').read_bytes(),scene_dll_sha256=sha(scene_path),witness_sha256=sha(folder/'difference-witness-report.json'),script_sha256=sha(Path(__file__)),full_scene_60fps=False)
 (folder/'source-difference-analysis.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='raw_components'},indent=2));print(json.dumps([x for x in raw if x['differences']],indent=2))
finally:
 for scene in scenes:fn(d,'nf_pc_scene_free',[P],None)(scene)
 for frame in frames:fn(d,'nf_pc_source_frame_free',[P],None)(frame)
