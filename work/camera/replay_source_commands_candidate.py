"""Offscreen diagnostic replay of owned source commands; no emulation/presentation."""
import ctypes as C,struct,json,hashlib
from pathlib import Path
p=Path('work/camera');run=p/'prototype-runs';records=list(struct.iter_unpack('<II12dQQ',(run/'source-command-state-records.bin').read_bytes()));payload=(run/'source-command-state-payload.bin').read_bytes()
gpu=C.CDLL(str((p/'owned-gpu-playable-input-profile-candidate.dll').resolve()));assert gpu.nf_owned_gpu_window(0)==0
gl=C.WinDLL('opengl32');gl.wglGetProcAddress.argtypes=[C.c_char_p];gl.wglGetProcAddress.restype=C.c_void_p
U=C.c_uint;I=C.c_int;F=C.c_float;D=C.c_double;P=C.c_void_p;cache={}
def function(name,args,ret=None):
 if name not in cache:
  try:f=getattr(gl,name);f.argtypes=args;f.restype=ret
  except AttributeError:
   ptr=gl.wglGetProcAddress(name.encode());assert ptr and ptr not in (1,2,3,C.c_void_p(-1).value),name;f=C.WINFUNCTYPE(ret,*args)(ptr)
  cache[name]=f
 return cache[name]
get_attachment=function('glGetFramebufferAttachmentParameteriv',[U,U,U,P]);target=I();get_attachment(0x8d40,0x8ce0,0x8cd1,C.byref(target));assert target.value
textures={};shaders={};programs={};locations={};current_program=0;images=[];identity=None
simple={10:('glBegin',[U]),11:('glEnd',[]),12:('glVertex2d',[D,D]),13:('glVertex2i',[I,I]),14:('glTexCoord2i',[I,I]),15:('glTexCoord4d',[D,D,D,D]),16:('glColor4f',[F,F,F,F]),17:('glColor3f',[F,F,F]),18:('glColor3ub',[C.c_ubyte]*3),19:('glEnable',[U]),20:('glDisable',[U]),21:('glScissor',[I,I,I,I]),23:('glTexParameteri',[U,U,I]),24:('glBlendFunc',[U,U]),25:('glAlphaFunc',[U,F]),26:('glMatrixMode',[U]),27:('glLoadIdentity',[]),28:('glOrtho',[D]*6),29:('glPushMatrix',[]),30:('glPopMatrix',[]),31:('glPushAttrib',[U]),32:('glPopAttrib',[]),33:('glViewport',[I]*4),34:('glClear',[U]),35:('glClearColor',[F]*4),36:('glPixelStorei',[U,I]),37:('glCopyTexImage2D',[U,I,U,I,I,I,I,I]),38:('glCopyTexSubImage2D',[U,I,I,I,I,I,I,I]),211:('glActiveTexture',[U])}
def snapshot():
 function('glPixelStorei',[U,I])(0x0d05,1);raw=C.create_string_buffer(3840*2160*3);function('glReadPixels',[I,I,I,I,U,U,P])(0,0,3840,2160,0x1907,0x1401,raw)
 err=function('glGetError',[],U)();assert err==0,(identity,hex(err))
 owned_rgb=raw.raw;rgb=b''.join(owned_rgb[y*11520:(y+1)*11520] for y in range(2159,-1,-1));return hashlib.sha256(rgb).hexdigest()
try:
 for record in records:
  op,n=record[:2];a=list(record[2:2+n]);offset,size=record[-2:];assert offset+size<=len(payload);data=payload[offset:offset+size]
  if op==1:identity=[int(x) for x in a]
  elif op==2:assert identity==[int(x) for x in a];images.append(snapshot())
  elif op in simple:
   name,types=simple[op];function(name,types)(*[int(x) if t not in (F,D) else x for x,t in zip(a,types)])
  elif op==110:
   ids=struct.unpack('<'+'I'*(size//4),data)
   for old in ids:
    if old==1:textures[old]=target.value
    else:
     new=U();function('glGenTextures',[I,P])(1,C.byref(new));textures[old]=new.value
  elif op==111:
   for old in struct.unpack('<'+'I'*(size//4),data):
    if old and old!=1:new=U(textures[old]);function('glDeleteTextures',[I,P])(1,C.byref(new))
  elif op==22:function('glBindTexture',[U,U])(int(a[0]),textures.get(int(a[1]),0))
  elif op in (100,101):
   buffer=C.create_string_buffer(data) if size else None
   if op==100:function('glTexImage2D',[U,I,I,I,I,I,U,U,P])(*map(int,a),buffer)
   else:function('glTexSubImage2D',[U,I,I,I,I,I,U,U,P])(*map(int,a),buffer)
  elif op==200:shaders[int(a[1])]=function('glCreateShader',[U],U)(int(a[0]))
  elif op==201:programs[int(a[0])]=function('glCreateProgram',[],U)()
  elif op==202:
   text=C.c_char_p(data);function('glShaderSource',[U,I,P,P])(shaders[int(a[0])],1,C.byref(text),None)
  elif op==203:function('glCompileShader',[U])(shaders[int(a[0])])
  elif op==204:function('glAttachShader',[U,U])(programs[int(a[0])],shaders[int(a[1])])
  elif op==205:
   pr=programs[int(a[0])];function('glLinkProgram',[U])(pr);ok=I();function('glGetProgramiv',[U,U,P])(pr,0x8b82,C.byref(ok));assert ok.value
  elif op==206:
   current_program=int(a[0]);function('glUseProgram',[U])(programs.get(current_program,0))
  elif op==207:locations[(int(a[0]),int(a[1]))]=function('glGetUniformLocation',[U,C.c_char_p],I)(programs[int(a[0])],data)
  elif op in (208,209,210):
   name,types={208:('glUniform1i',[I,I]),209:('glUniform2f',[I,F,F]),210:('glUniform4f',[I,F,F,F,F])}[op]
   function(name,types)(locations[current_program,int(a[0])],*[int(x) if t==I else x for x,t in zip(a[1:],types[1:])])
  elif op==212:function('glDeleteShader',[U])(shaders[int(a[0])])
  elif op==213:function('glDeleteProgram',[U])(programs[int(a[0])])
  else:raise AssertionError(('Unknown replay opcode',op))
 baseline=json.loads((run/'source-command-state-component.json').read_text());expected=[x['source_rgb_sha256'] for x in baseline['checks']];assert len(images)==5
 result=dict(result='PASS_EXACT_4K_SOURCE_COMMAND_REPLAY' if images==expected else 'FAIL_REPLAY_PIXEL_PARITY',images=images,expected=expected,matching_frames=sum(a==b for a,b in zip(images,expected)),commands=len(records),scope='Fresh native GL context replay from owned commands; diagnostic readback only, no D3D or playable/cadence claim.')
 (run/'source-command-replay.json').write_text(json.dumps(result,indent=2));print(result)
 assert images==expected,'Command replay differs from actual complete source frames'
finally:assert gpu.nf_owned_gpu_close()
