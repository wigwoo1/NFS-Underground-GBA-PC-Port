import struct,json,sys
from pathlib import Path

def validate(raw,payload):
 rows=list(struct.iter_unpack('<II12dQQ',raw));textures=set();shaders=set();programs=set();locations={};uniforms={};unit=0;bindings={};stack=[];program=0;shader_draws=0;uploads=0;markers=[]
 required={'nativeBackground','candidateColor','candidateMetadata','ownedText','ownedTextEnabled','backdropColor','effectParameters','firstTargets','secondTargets','coefficients'}
 for r in rows:
  op,n=r[:2];a=r[2:14];offset,size=r[-2:];assert n<=12 and offset+size<=len(payload),'Invalid owned payload bounds';data=payload[offset:offset+size]
  if op==1:markers.append(list(a[:3]))
  elif op==110:
   ids=struct.unpack('<'+'I'*(size//4),data);assert len(ids)==int(a[0]);assert all(x and x not in textures for x in ids);textures.update(ids)
  elif op==111:
   ids=struct.unpack('<'+'I'*(size//4),data);assert len(ids)==int(a[0])
   for t in ids:
    if t:assert t in textures,'Delete unknown texture';textures.remove(t)
   bindings={k:(0 if v in ids else v) for k,v in bindings.items()}
  elif op==211:unit=int(a[0])-0x84c0;assert 0<=unit<32
  elif op==22:
   t=int(a[1]);assert not t or t in textures,'Bind unknown texture';bindings[unit]=t
  elif op==31:stack.append((unit,bindings.copy()))
  elif op==32:assert stack;unit,bindings=stack.pop()
  elif op in (100,101):
   assert bindings.get(unit,0) in textures,'Upload without owned texture'
   if size:assert size==int(a[3 if op==100 else 4])*int(a[4 if op==100 else 5])*4
   uploads+=1
  elif op==200:shaders.add(int(a[1]))
  elif op==201:programs.add(int(a[0]))
  elif op==202:assert int(a[0]) in shaders and data.endswith(b'\0') and b'void main' in data
  elif op==203:assert int(a[0]) in shaders
  elif op==204:assert int(a[0]) in programs and int(a[1]) in shaders
  elif op==205:assert int(a[0]) in programs
  elif op==212:assert int(a[0]) in shaders;shaders.remove(int(a[0]))
  elif op==213:assert int(a[0]) in programs;programs.remove(int(a[0]))
  elif op==206:program=int(a[0]);assert not program or program in programs
  elif op==207:
   assert int(a[0]) in programs and data.endswith(b'\0');locations[(int(a[0]),int(a[1]))]=data[:-1].decode()
  elif op in (208,209,210):
   assert program in programs;name=locations.get((program,int(a[0])));assert name is not None,'Uniform location unrecorded';uniforms[(program,name)]=a[1:n]
  elif op in (12,13) and program:
   assert required.issubset({name for pr,name in uniforms if pr==program}),'Missing HUD uniform state'
   for name in ['nativeBackground','candidateColor','candidateMetadata']:
    assert bindings.get(int(uniforms[program,name][0]),0) in textures,'Missing sampler texture'
   shader_draws+=1
 assert not textures and not shaders and not programs and not stack,'Resources/state unbalanced'
 assert markers==[[1,1,i] for i in range(5)] and shader_draws>0
 return dict(result='PASS_SOURCE_COMMAND_RESOURCE_AND_HUD_STATE',commands=len(rows),owned_bytes=len(payload),uploads=uploads,hud_shader_vertices=shader_draws,markers=markers,scope='Actual captured five samples; resource and HUD state validation only, not full replay/D3D parity.')
if __name__=='__main__':
 p=Path('work/camera/prototype-runs');raw=(p/'source-command-state-records.bin').read_bytes();payload=(p/'source-command-state-payload.bin').read_bytes();r=validate(raw,payload)
 rows=list(struct.iter_unpack('<II12dQQ',raw));target=next(i for i,x in enumerate(rows) if x[0]==22);mut=bytearray(raw);struct.pack_into('<d',mut,target*120+16,999999)
 try:validate(mut,payload)
 except AssertionError:pass
 else:raise AssertionError('Unknown texture mutation accepted')
 mut=bytearray(raw);struct.pack_into('<Q',mut,104,len(payload)+1)
 try:validate(mut,payload)
 except AssertionError:pass
 else:raise AssertionError('Invalid payload mutation accepted')
 r['malformed_texture_and_payload_rejected']=True;(p/'source-command-state-validation.json').write_text(json.dumps(r,indent=2));print(r)
