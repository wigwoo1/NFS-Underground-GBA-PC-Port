from pathlib import Path
import ctypes as C, os, re, math
P=C.c_void_p;I=C.c_int;U=C.c_uint;F=C.c_float
class GLESModelReference:
 def __init__(self,java):
  self.directory=Path(r'C:\NFSUG-Workspace\android-tools\sdk\emulator\lib64\gles_swiftshader')
  with os.add_dll_directory(str(self.directory)):self.e=C.CDLL(str(self.directory/'libEGL.dll'));self.g=C.CDLL(str(self.directory/'libGLESv2.dll'))
  self.funcs={}
  def ef(name,args,result=I):v=getattr(self.e,name);v.argtypes=args;v.restype=result;return v
  self.make=ef('eglMakeCurrent',[P,P,P,P]);self.destroy_context=ef('eglDestroyContext',[P,P]);self.destroy_surface=ef('eglDestroySurface',[P,P]);self.terminate=ef('eglTerminate',[P]);self.display=ef('eglGetDisplay',[P],P)(None);assert self.display and ef('eglInitialize',[P,P,P])(self.display,None,None)
  config=P();count=I();attrs=(I*13)(0x3033,1,0x3040,4,0x3024,8,0x3023,8,0x3022,8,0x3021,8,0x3038);assert ef('eglChooseConfig',[P,P,P,I,P])(self.display,attrs,C.byref(config),1,C.byref(count)) and count.value
  self.surface=ef('eglCreatePbufferSurface',[P,P,P],P)(self.display,config,(I*5)(0x3057,1,0x3056,1,0x3038));self.context=ef('eglCreateContext',[P,P,P,P],P)(self.display,config,None,(I*3)(0x3098,2,0x3038));assert self.surface and self.context;self.current()
  self.renderer=self.call('glGetString',[U],C.c_char_p,0x1f01).decode();self.version=self.call('glGetString',[U],C.c_char_p,0x1f02).decode()
  text=java.read_text();strings=re.findall(r'shader\(GLES20\.GL_(?:VERTEX|FRAGMENT)_SHADER,"([^"]+)"\)',text);assert len(strings)==2
  self.shaders=strings;self.program=self.call('glCreateProgram',[],U)
  for kind,code in zip([0x8b31,0x8b30],strings):
   sh=self.call('glCreateShader',[U],U,kind);raw=C.c_char_p(code.encode());self.call('glShaderSource',[U,I,P,P],None,sh,1,C.byref(raw),None);self.call('glCompileShader',[U],None,sh);ok=I();self.call('glGetShaderiv',[U,U,P],None,sh,0x8b81,C.byref(ok));assert ok.value,'Reference shader compile';self.call('glAttachShader',[U,U],None,self.program,sh);self.call('glDeleteShader',[U],None,sh)
  for index,name in enumerate([b'p',b't']):self.call('glBindAttribLocation',[U,U,C.c_char_p],None,self.program,index,name)
  self.call('glLinkProgram',[U],None,self.program);ok=I();self.call('glGetProgramiv',[U,U,P],None,self.program,0x8b82,C.byref(ok));assert ok.value
  self.textures=(U*3)();self.call('glGenTextures',[I,P],None,3,self.textures);self.fbo=U();self.call('glGenFramebuffers',[I,P],None,1,C.byref(self.fbo))
 def call(self,name,args,result,*values):
  if name not in self.funcs:v=getattr(self.g,name);v.argtypes=args;v.restype=result;self.funcs[name]=v
  return self.funcs[name](*values)
 def current(self):assert self.make(self.display,self.surface,self.surface,self.context)
 def uniform(self,name):return self.call('glGetUniformLocation',[U,C.c_char_p],I,self.program,name.encode())
 def tex(self,unit,texture,w,h,data):
  self.call('glActiveTexture',[U],None,0x84c0+unit);self.call('glBindTexture',[U,U],None,0xde1,texture)
  for key,value in [(0x2801,0x2600),(0x2800,0x2600),(0x2802,0x812f),(0x2803,0x812f)]:self.call('glTexParameteri',[U,U,I],None,0xde1,key,value)
  self.call('glTexImage2D',[U,I,I,I,I,I,U,U,P],None,0xde1,0,0x1908,w,h,0,0x1908,0x1401,data)
 def render(self,vertices,planes,rgba,indices,palette,tw,th,w,h,aw,ah,top,bottom):
  self.current();self.tex(0,self.textures[2],w,h,None);self.call('glBindFramebuffer',[U,U],None,0x8d40,self.fbo);self.call('glFramebufferTexture2D',[U,U,U,U,I],None,0x8d40,0x8ce0,0xde1,self.textures[2],0);assert self.call('glCheckFramebufferStatus',[U],U,0x8d40)==0x8cd5
  for flag in [0xbe2,0xb71,0xb44,0xc11,0xbd0]:self.call('glDisable',[U],None,flag)
  self.call('glViewport',[I,I,I,I],None,0,0,w,h);self.call('glClearColor',[F,F,F,F],None,0,0,0,0);self.call('glClear',[U],None,0x4000);self.call('glUseProgram',[U],None,self.program);self.call('glPixelStorei',[U,I],None,0xcf5,1)
  if indices:
   data=bytearray(len(indices)*4)
   for i,index in enumerate(indices):data[i*4]=index;data[i*4+3]=255
   rgba=bytes(data)
  self.tex(0,self.textures[0],tw,th,rgba);self.tex(1,self.textures[1],256,160,palette)
  for name,value in [('image',0),('zeroRows',1)]:self.call('glUniform1i',[I,I],None,self.uniform(name),value)
  for name,value in [('height',ah),('viewportWidth',aw),('wall',0),('indexed',int(bool(indices)))]:self.call('glUniform1f',[I,F],None,self.uniform(name),value)
  self.call('glViewport',[I,I,I,I],None,0,0,aw,ah);t=math.ceil(top*ah/160-.5);b=math.ceil(bottom*ah/160-.5);self.call('glEnable',[U],None,0xc11);self.call('glScissor',[I,I,I,I],None,0,ah-b,aw,b-t)
  storage=C.create_string_buffer(vertices);self.call('glBindBuffer',[U,U],None,0x8892,0)
  for attr,size,offset in [(0,2,0),(1,3,8)]:self.call('glVertexAttribPointer',[U,I,U,U,I,P],None,attr,size,0x1406,0,20,C.addressof(storage)+offset);self.call('glEnableVertexAttribArray',[U],None,attr)
  for tri in range(len(planes)//44):
   plane=(F*11).from_buffer_copy(planes[tri*44:(tri+1)*44]);self.call('glUniform2f',[I,F,F],None,self.uniform('origin'),plane[0],plane[1])
   for name,offset in [('planeBase',8),('planeX',20),('planeY',32)]:self.call('glUniform3fv',[I,I,P],None,self.uniform(name),1,C.addressof(plane)+offset)
   self.call('glDrawArrays',[U,I,I],None,4,tri*3,3)
  output=(C.c_ubyte*(w*h*4))();self.call('glPixelStorei',[U,I],None,0xd05,1);self.call('glReadPixels',[I,I,I,I,U,U,P],None,0,0,w,h,0x1908,0x1401,output);assert self.call('glGetError',[],U)==0;return bytes(output)
 def close(self):
  self.current();self.call('glDeleteProgram',[U],None,self.program);self.call('glDeleteTextures',[I,P],None,3,self.textures);self.call('glDeleteFramebuffers',[I,P],None,1,C.byref(self.fbo));self.make(self.display,None,None,None);self.destroy_context(self.display,self.context);self.destroy_surface(self.display,self.surface);self.terminate(self.display)
