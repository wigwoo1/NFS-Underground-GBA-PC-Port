"""Normalize owned source commands for GPU backends; no image matching."""
import struct,json,copy,hashlib,math
from pathlib import Path

def normalize(raw,payload):
 records=list(struct.iter_unpack('<II12dQQ',raw));ops=[];textures={};versions={};uniforms={};locations={};program=0;shaders={};shader_sources={};attachments={};identities=[]
 state=dict(unit=0,bindings={},enabled=[],color=[1.,1.,1.,1.],texcoord=[0.,0.,0.,1.],viewport=[0,0,3840,2160],scissor=[0,0,3840,2160],blend=[1,0],alpha=[0x207,0.],matrix_mode=0x1700)
 matrices={0x1700:None,0x1701:None};matrix_stacks={0x1700:[],0x1701:[]};stack=[];primitive=None;vertices=[];clear_color=[0.,0.,0.,0.]
 def resource(t):assert t in textures;return [t,versions[t]]
 def update(t,kind,args,data):
  versions[t]+=1;ops.append(dict(op=kind,target=resource(t),args=args,payload_offset=data[0],payload_bytes=data[1]))
 for index,r in enumerate(records):
  code,n=r[:2];a=list(r[2:2+n]);offset,size=r[-2:];assert n<=12 and offset+size<=len(payload);data=payload[offset:offset+size]
  if code in (1,2):
   key=[int(x) for x in a];identities.append((code,key));ops.append(dict(op='begin_frame' if code==1 else 'end_frame',identity=key))
  elif code==110:
   for t in struct.unpack('<'+'I'*(size//4),data):assert t not in textures;textures[t]={};versions[t]=0;ops.append(dict(op='create_texture',id=t))
  elif code==111:
   for t in struct.unpack('<'+'I'*(size//4),data):
    if t:assert t in textures;ops.append(dict(op='delete_texture',id=t));del textures[t];state['bindings']={k:(0 if v==t else v) for k,v in state['bindings'].items()}
  elif code==211:state['unit']=int(a[0])-0x84c0
  elif code==22:
   t=int(a[1]);assert not t or t in textures;state['bindings'][state['unit']]=t
  elif code==23:
   t=state['bindings'][state['unit']];assert t in textures;textures[t][int(a[1])]=int(a[2])
  elif code in (100,101):
   t=state['bindings'][state['unit']];update(t,'allocate_texture' if code==100 else 'update_texture',a,(offset,size))
  elif code in (37,38):
   t=state['bindings'][state['unit']];update(t,'copy_render_target',a,(0,0));ops[-1]['source_render_target']=1;ops[-1]['copy_kind']=code
  elif code==200:shaders[int(a[1])]=int(a[0])
  elif code==201:attachments[int(a[0])]=[]
  elif code==202:shader_sources[int(a[0])]=[offset,size]
  elif code==203:assert int(a[0]) in shaders
  elif code==204:attachments[int(a[0])].append(int(a[1]))
  elif code==205:
   pr=int(a[0]);sources=[dict(stage=shaders[s],offset=shader_sources[s][0],bytes=shader_sources[s][1]) for s in attachments[pr]];ops.append(dict(op='create_program',id=pr,sources=sources))
  elif code==212:pass # linked program retains shader source semantics
  elif code==213:ops.append(dict(op='delete_program',id=int(a[0])))
  elif code==206:program=int(a[0])
  elif code==207:locations[int(a[0]),int(a[1])]=data[:-1].decode()
  elif code in (208,209,210):uniforms[program,locations[program,int(a[0])]]=a[1:]
  elif code in (19,20):
   cap=int(a[0]);s=set(state['enabled']);s.add(cap) if code==19 else s.discard(cap);state['enabled']=sorted(s)
  elif code==21:state['scissor']=list(map(int,a))
  elif code==24:state['blend']=list(map(int,a))
  elif code==25:state['alpha']=a
  elif code==26:state['matrix_mode']=int(a[0]);assert state['matrix_mode'] in matrices
  elif code==27:matrices[state['matrix_mode']]=None
  elif code==28:assert matrices[state['matrix_mode']] is None and state['matrix_mode']==0x1701;matrices[0x1701]=a
  elif code==29:matrix_stacks[state['matrix_mode']].append(copy.deepcopy(matrices[state['matrix_mode']]))
  elif code==30:matrices[state['matrix_mode']]=matrix_stacks[state['matrix_mode']].pop()
  elif code==31:assert int(a[0])==0xfffff;stack.append(copy.deepcopy(state))
  elif code==32:state=stack.pop()
  elif code==33:state['viewport']=list(map(int,a))
  elif code==35:clear_color=a
  elif code==34:assert int(a[0])==0x4000;ops.append(dict(op='clear',target=1,color=clear_color[:]))
  elif code==36:assert list(map(int,a))==[0x0d05,1] or list(map(int,a))==[0x0cf5,1],('Unsupported pixel storage',a)
  elif code in (16,17,18):state['color']=([x/255 for x in a] if code==18 else a)+([] if len(a)==4 else [1.])
  elif code in (14,15):state['texcoord']=a if code==15 else a+[0.,1.]
  elif code==10:assert primitive is None;primitive=int(a[0]);assert primitive in (4,6,7);vertices=[]
  elif code in (12,13):assert primitive is not None;vertices.append(a+state['texcoord']+state['color'])
  elif code==11:
   assert primitive is not None and matrices[0x1700] is None and matrices[0x1701] is not None
   if primitive==4:
    assert len(vertices)%3==0;indices=list(range(len(vertices)))
   elif primitive==7:
    assert len(vertices)%4==0;indices=[k+j for k in range(0,len(vertices),4) for j in (0,1,3,1,2,3)]
   else:indices=[j for k in range(1,len(vertices)-1) for j in (0,k,k+1)]
   assert all(math.isfinite(x) for v in vertices for x in v)
   units={str(k):dict(resource=resource(t),sampler=copy.deepcopy(textures[t])) for k,t in state['bindings'].items() if t}
   ops.append(dict(op='draw_triangles',target=1,vertices=vertices,indices=indices,state=copy.deepcopy(state),projection=matrices[0x1701][:],program=program,uniforms={name:value[:] for (pr,name),value in uniforms.items() if pr==program},textures=units,source_command=index,source_primitive=primitive));primitive=None
  else:raise AssertionError(('Unhandled source opcode',code))
 assert primitive is None and not textures and not stack and all(not x for x in matrix_stacks.values())
 assert identities==sum(([ (1,[1,1,i]),(2,[1,1,i]) ] for i in range(5)),[])
 return dict(version=1,target_size=[3840,2160],vertex_format=['x','y','s','t','r','q','red','green','blue','alpha'],ops=ops,scope='Actual source command normalization, not D3D rendering or raster parity proof.')
if __name__=='__main__':
 p=Path('work/camera/prototype-runs');raw=(p/'source-command-state-records.bin').read_bytes();payload=(p/'source-command-state-payload.bin').read_bytes();r=normalize(raw,payload);draws=[x for x in r['ops'] if x['op']=='draw_triangles'];assert len(draws)==1211 and sum(x['program']!=0 for x in draws)==180
 (p/'normalized-source-gpu-packets.json').write_text(json.dumps(r,separators=(',',':')))
 stats=dict(result='PASS_SOURCE_GPU_PACKET_NORMALIZATION',draws=len(draws),triangles=sum(len(x['indices'])//3 for x in draws),hud_draws=sum(x['program']!=0 for x in draws),projective_draws=sum(any(v[5]!=1 for v in x['vertices']) for x in draws),ops=len(r['ops']),scope=r['scope']);(p/'normalized-source-gpu-packets-audit.json').write_text(json.dumps(stats,indent=2));print(stats)


