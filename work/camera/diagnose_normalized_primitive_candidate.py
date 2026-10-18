"""Diagnostic GL raster check of normalized Direct3D-bound triangle packets."""
from pathlib import Path
import json,ctypes as C
p=Path('work/camera');source=(p/'replay_source_commands_candidate.py').read_text();exec(compile(source.split('try:\n for record in records:')[0],'replay_helpers','exec'))
packet=json.loads((run/'normalized-source-gpu-packets.json').read_text());textures={};programs={};images=[];identity=None
try:
 for op in packet['ops']:
  kind=op['op']
  if kind=='create_texture':
   old=op['id']
   if old==1:textures[old]=target.value
   else:new=U();function('glGenTextures',[I,P])(1,C.byref(new));textures[old]=new.value
  elif kind=='delete_texture':
   old=op['id']
   if old!=1:new=U(textures[old]);function('glDeleteTextures',[I,P])(1,C.byref(new))
  elif kind in ('allocate_texture','update_texture','copy_render_target'):
   function('glActiveTexture',[U])(0x84c0);function('glBindTexture',[U,U])(0x0de1,textures[op['target'][0]]);a=list(map(int,op['args']));offset=op['payload_offset'];size=op['payload_bytes'];data=payload[offset:offset+size];buffer=C.create_string_buffer(data) if size else None
   if kind=='allocate_texture':function('glTexImage2D',[U,I,I,I,I,I,U,U,P])(*a,buffer)
   elif kind=='update_texture':function('glTexSubImage2D',[U,I,I,I,I,I,U,U,P])(*a,buffer)
   else:
    name,types=simple[op['copy_kind']];function(name,types)(*a)
  elif kind=='create_program':
   pr=function('glCreateProgram',[],U)();programs[op['id']]=pr;ss=[]
   for item in op['sources']:
    sh=function('glCreateShader',[U],U)(item['stage']);text=C.c_char_p(payload[item['offset']:item['offset']+item['bytes']]);function('glShaderSource',[U,I,P,P])(sh,1,C.byref(text),None);function('glCompileShader',[U])(sh);function('glAttachShader',[U,U])(pr,sh);ss.append(sh)
   function('glLinkProgram',[U])(pr);ok=I();function('glGetProgramiv',[U,U,P])(pr,0x8b82,C.byref(ok));assert ok.value
   for sh in ss:function('glDeleteShader',[U])(sh)
  elif kind=='delete_program':function('glDeleteProgram',[U])(programs[op['id']])
  elif kind=='begin_frame':identity=op['identity']
  elif kind=='end_frame':assert identity==op['identity'];images.append(snapshot())
  elif kind=='clear':function('glDisable',[U])(0x0c11);function('glClearColor',[F]*4)(*op['color']);function('glClear',[U])(0x4000)
  elif kind=='draw_triangles':
   s=op['state'];function('glActiveTexture',[U])(0x84c0)
   for cap in (0x0bc0,0x0be2,0x0c11,0x0b71,0x0de1):function('glEnable' if cap in s['enabled'] else 'glDisable',[U])(cap)
   function('glScissor',[I]*4)(*s['scissor']);function('glViewport',[I]*4)(*s['viewport']);function('glBlendFunc',[U,U])(*s['blend']);function('glAlphaFunc',[U,F])(int(s['alpha'][0]),s['alpha'][1])
   function('glMatrixMode',[U])(0x1701);function('glLoadIdentity',[])();function('glOrtho',[D]*6)(*op['projection']);function('glMatrixMode',[U])(0x1700);function('glLoadIdentity',[])()
   for unit,tex in op['textures'].items():
    function('glActiveTexture',[U])(0x84c0+int(unit));function('glBindTexture',[U,U])(0x0de1,textures[tex['resource'][0]])
    for name,value in tex['sampler'].items():function('glTexParameteri',[U,U,I])(0x0de1,int(name),value)
   pr=programs.get(op['program'],0);function('glUseProgram',[U])(pr)
   if pr:
    for name,values in op['uniforms'].items():
     loc=function('glGetUniformLocation',[U,C.c_char_p],I)(pr,name.encode());assert loc>=0
     if len(values)==1:function('glUniform1i',[I,I])(loc,int(values[0]))
     else:function('glUniform4f',[I,F,F,F,F])(loc,*values)
   function('glActiveTexture',[U])(0x84c0);function('glBegin',[U])(op['source_primitive'])
   for index in range(len(op['vertices'])):
    v=op['vertices'][index];function('glColor4f',[F]*4)(*v[6:10]);function('glTexCoord4d',[D]*4)(*v[2:6]);function('glVertex2d',[D,D])(*v[:2])
   function('glEnd',[])();function('glUseProgram',[U])(0)
  else:raise AssertionError(kind)
 expected=[x['source_rgb_sha256'] for x in json.loads((run/'source-command-state-component.json').read_text())['checks']]
 result=dict(result='PASS_NORMALIZED_GPU_TRIANGLE_PACKET_4K_PARITY' if images==expected else 'FAIL_NORMALIZED_PIXEL_PARITY',matching_frames=sum(a==b for a,b in zip(images,expected)),images=images,expected=expected,scope='Normalized triangles/textures/HUD replayed with GL; not D3D or live cadence proof.');(run/'normalized-source-gpu-packet-replay.json').write_text(json.dumps(result,indent=2));print(result);assert images==expected
finally:assert gpu.nf_owned_gpu_close()
