from gles_model_reference import GLESModelReference,P,I,U,F,C
import re,math,struct
import numpy as np
class GLESSceneReference(GLESModelReference):
 def __init__(self,java,rgba_java,edge_java=None,hud_java=None):
  super().__init__(java);strings=re.findall(r'shader\(GLES20\.GL_(?:VERTEX|FRAGMENT)_SHADER,"([^"]+)"\)',rgba_java.read_text());assert len(strings)==2;self.background_program=self.call('glCreateProgram',[],U)
  for kind,code in zip([0x8b31,0x8b30],strings):
   shader=self.call('glCreateShader',[U],U,kind);raw=C.c_char_p(code.encode());self.call('glShaderSource',[U,I,P,P],None,shader,1,C.byref(raw),None);self.call('glCompileShader',[U],None,shader);ok=I();self.call('glGetShaderiv',[U,U,P],None,shader,0x8b81,C.byref(ok));assert ok.value;self.call('glAttachShader',[U,U],None,self.background_program,shader);self.call('glDeleteShader',[U],None,shader)
  self.call('glBindAttribLocation',[U,U,C.c_char_p],None,self.background_program,0,b'p');self.call('glLinkProgram',[U],None,self.background_program);ok=I();self.call('glGetProgramiv',[U,U,P],None,self.background_program,0x8b82,C.byref(ok));assert ok.value
  self.edge_program=0
  if edge_java:
   strings=re.findall(r'shader\(GLES20\.GL_(?:VERTEX|FRAGMENT)_SHADER,"([^"]+)"\)',edge_java.read_text());assert len(strings)==2;self.edge_program=self.call('glCreateProgram',[],U)
   for kind,code in zip([0x8b31,0x8b30],strings):
    shader=self.call('glCreateShader',[U],U,kind);raw=C.c_char_p(code.encode());self.call('glShaderSource',[U,I,P,P],None,shader,1,C.byref(raw),None);self.call('glCompileShader',[U],None,shader);ok=I();self.call('glGetShaderiv',[U,U,P],None,shader,0x8b81,C.byref(ok));assert ok.value;self.call('glAttachShader',[U,U],None,self.edge_program,shader);self.call('glDeleteShader',[U],None,shader)
   for attr,name in [(0,b'p'),(1,b'uv')]:self.call('glBindAttribLocation',[U,U,C.c_char_p],None,self.edge_program,attr,name)
   self.call('glLinkProgram',[U],None,self.edge_program);ok=I();self.call('glGetProgramiv',[U,U,P],None,self.edge_program,0x8b82,C.byref(ok));assert ok.value
  self.hud_program=0;self.hudcopy=U()
  if hud_java:
   text=hud_java.read_text();vertex=re.findall(r'shader\(GLES20.GL_VERTEX_SHADER,"([^"]+)"\)',text);assert len(vertex)==1;fragment=re.search(r'FRAGMENT="([^"]+)"',text).group(1);self.hud_program=self.call('glCreateProgram',[],U)
   for kind,code in zip([0x8b31,0x8b30],[vertex[0],fragment]):
    shader=self.call('glCreateShader',[U],U,kind);raw=C.c_char_p(code.encode());self.call('glShaderSource',[U,I,P,P],None,shader,1,C.byref(raw),None);self.call('glCompileShader',[U],None,shader);ok=I();self.call('glGetShaderiv',[U,U,P],None,shader,0x8b81,C.byref(ok));assert ok.value;self.call('glAttachShader',[U,U],None,self.hud_program,shader);self.call('glDeleteShader',[U],None,shader)
   self.call('glBindAttribLocation',[U,U,C.c_char_p],None,self.hud_program,0,b'p');self.call('glLinkProgram',[U],None,self.hud_program);ok=I();self.call('glGetProgramiv',[U,U,P],None,self.hud_program,0x8b82,C.byref(ok));assert ok.value;self.call('glGenTextures',[I,P],None,1,C.byref(self.hudcopy))
 def draw_hud(self,scene,w,h,aw,ah):
  hud=scene.get('hud')
  if not hud:return
  assert self.hud_program;self.call('glUseProgram',[U],None,self.hud_program);self.tex(0,self.hudcopy,w,h,None);self.call('glCopyTexImage2D',[U,I,U,I,I,I,I,I],None,0xde1,0,0x1908,0,0,w,h,0);self.tex(1,self.textures[0],240,160,hud['colors']);self.tex(2,self.textures[1],240,160,hud['metadata'])
  uniform=lambda n:self.call('glGetUniformLocation',[U,C.c_char_p],I,self.hud_program,n.encode())
  for name,value in [('nativeBackground',0),('candidates',1),('metadataImage',2)]:self.call('glUniform1i',[I,I],None,uniform(name),value)
  for name,x,y in [('viewport',aw,ah),('target',w,h)]:self.call('glUniform2f',[I,F,F],None,uniform(name),x,y)
  quad=(F*8)(-1,-1,1,-1,-1,1,1,1);self.call('glDisableVertexAttribArray',[U],None,1);self.call('glVertexAttribPointer',[U,I,U,U,I,P],None,0,2,0x1406,0,0,quad);self.call('glEnableVertexAttribArray',[U],None,0);self.call('glEnable',[U],None,0xc11);y=0
  while y<160:
   p=hud['parameters'][y];end=y+1
   while end<160 and hud['parameters'][end]==p:end+=1
   top=math.ceil(y*ah/160-.5);bottom=math.ceil(end*ah/160-.5)
   if top<bottom:
    blend=p[2];alpha=p[3]
    for name,values in [('backdropColor',(p[0]&255,(p[0]>>8)&255,(p[0]>>16)&255,1)),('effectParameters',((blend>>6)&3,0,0,p[1])),('firstTargets',(bool(blend&16),bool(blend&4),bool(blend&32),0)),('secondTargets',(bool(blend&4096),bool(blend&1024),bool(blend&8192),0)),('coefficients',(min(alpha&31,16),min((alpha>>8)&31,16),min(p[4]&31,16),0))]:self.call('glUniform4f',[I,F,F,F,F],None,uniform(name),*values)
    self.call('glScissor',[I,I,I,I],None,0,ah-bottom,aw,bottom-top);self.call('glDrawArrays',[U,I,I],None,5,0,4)
   y=end
  self.call('glDisable',[U],None,0xc11)
 def draw_retained(self,scene,aw,ah):
  if not scene.get('retained'):return
  assert self.edge_program;self.call('glUseProgram',[U],None,self.edge_program);self.tex(1,self.textures[1],256,160,scene['palette'])
  uniform=lambda n:self.call('glGetUniformLocation',[U,C.c_char_p],I,self.edge_program,n.encode())
  for name,value in [('indices',0),('palette',1)]:self.call('glUniform1i',[I,I],None,uniform(name),value)
  self.call('glUniform1f',[I,F],None,uniform('height'),ah);self.call('glDisable',[U],None,0xc11)
  for draw in scene['retained']:
   if 'vertices' not in draw:
    source=draw['source'];tw=1024;th=(len(source)+tw-1)//tw;indexed=np.zeros((tw*th,4),np.uint8);indexed[:len(source),0]=np.frombuffer(source,np.uint8);indexed[:len(source),3]=255;draw['rgba']=indexed.tobytes();draw['height']=th
    records=np.frombuffer(draw['records'],'<i4').reshape(-1,3);assert np.all((records[:,1]>=draw['top'])&(records[:,1]<draw['bottom']));v=np.empty((len(records),6,4),np.float32);v[:,:,:2]=records[:,None,:2]+np.array([[0,0],[1,0],[0,1],[0,1],[1,0],[1,1]],np.float32)[None,:,:];v[:,:,2]=((records[:,2]%tw).astype(np.float32)+np.float32(.5))[:,None]/np.float32(tw);v[:,:,3]=((records[:,2]//tw).astype(np.float32)+np.float32(.5))[:,None]/np.float32(th);draw['vertices']=v.tobytes();draw['count']=len(records)*6
   self.tex(0,self.textures[0],1024,draw['height'],draw['rgba']);storage=C.create_string_buffer(draw['vertices'])
   for attr,offset in [(0,0),(1,8)]:self.call('glVertexAttribPointer',[U,I,U,U,I,P],None,attr,2,0x1406,0,16,C.addressof(storage)+offset);self.call('glEnableVertexAttribArray',[U],None,attr)
   self.call('glDrawArrays',[U,I,I],None,4,0,draw['count'])
 def render_scene(self,scene,w,h,aw,ah):
  self.current();self.tex(0,self.textures[2],w,h,None);self.call('glBindFramebuffer',[U,U],None,0x8d40,self.fbo);self.call('glFramebufferTexture2D',[U,U,U,U,I],None,0x8d40,0x8ce0,0xde1,self.textures[2],0);assert self.call('glCheckFramebufferStatus',[U],U,0x8d40)==0x8cd5
  for flag in [0xbe2,0xb71,0xb44,0xc11,0xbd0]:self.call('glDisable',[U],None,flag)
  self.call('glViewport',[I,I,I,I],None,0,0,w,h);self.call('glClearColor',[F,F,F,F],None,0,0,0,0);self.call('glClear',[U],None,0x4000);self.call('glPixelStorei',[U,I],None,0xcf5,1);self.call('glViewport',[I,I,I,I],None,0,0,aw,ah);self.call('glUseProgram',[U],None,self.background_program);self.tex(0,self.textures[0],240,160,scene['background'])
  uniform=lambda n:self.call('glGetUniformLocation',[U,C.c_char_p],I,self.background_program,n.encode())
  self.call('glUniform1i',[I,I],None,uniform('image'),0);self.call('glUniform2f',[I,F,F],None,uniform('viewport'),aw,ah);quad=(F*8)(-1,-1,1,-1,-1,1,1,1);self.call('glBindBuffer',[U,U],None,0x8892,0);self.call('glDisableVertexAttribArray',[U],None,1);self.call('glVertexAttribPointer',[U,I,U,U,I,P],None,0,2,0x1406,0,0,quad);self.call('glEnableVertexAttribArray',[U],None,0);self.call('glDrawArrays',[U,I,I],None,5,0,4)
  self.draw_retained(scene,aw,ah)
  self.call('glUseProgram',[U],None,self.program);self.tex(1,self.textures[1],256,160,scene['palette'])
  for name,value in [('image',0),('zeroRows',1)]:self.call('glUniform1i',[I,I],None,self.uniform(name),value)
  for name,value in [('height',ah),('viewportWidth',aw)]:self.call('glUniform1f',[I,F],None,self.uniform(name),value)
  for command in scene['commands']:
   m=command['info']
   if not m[5]:continue
   top=max(m[11],m[13]);bottom=min(m[12],m[14]);left=math.ceil(m[9]*aw/240-.5);right=math.ceil(m[10]*aw/240-.5);t=math.ceil(top*ah/160-.5);b=math.ceil(bottom*ah/160-.5)
   if top>=bottom or left>=right or t>=b:continue
   for name,value in [('wall',m[7]),('indexed',m[6])]:self.call('glUniform1f',[I,F],None,self.uniform(name),value)
   self.call('glEnable',[U],None,0xc11);storage=C.create_string_buffer(command['vertices'])
   for attr,size,offset in [(0,2,0),(1,3,8)]:self.call('glVertexAttribPointer',[U,I,U,U,I,P],None,attr,size,0x1406,0,20,C.addressof(storage)+offset);self.call('glEnableVertexAttribArray',[U],None,attr)
   shade=command['columns'].get(aw);start=left
   while start<right:
    level=shade[start] if shade else 0;end=right
    if shade:
     end=start+1
     while end<right and shade[end]==level:end+=1
    self.tex(0,self.textures[0],m[3],m[4],command['images'][level]);self.call('glScissor',[I,I,I,I],None,start,ah-b,end-start,b-t)
    for triangle in range(m[5]//3):
     plane=(F*11).from_buffer_copy(command['planes'][triangle*44:(triangle+1)*44]);self.call('glUniform2f',[I,F,F],None,self.uniform('origin'),plane[0],plane[1])
     for name,offset in [('planeBase',8),('planeX',20),('planeY',32)]:self.call('glUniform3fv',[I,I,P],None,self.uniform(name),1,C.addressof(plane)+offset)
     self.call('glDrawArrays',[U,I,I],None,4,triangle*3,3)
    start=end
  self.draw_hud(scene,w,h,aw,ah)
  output=(C.c_ubyte*(w*h*4))();self.call('glPixelStorei',[U,I],None,0xd05,1);self.call('glReadPixels',[I,I,I,I,U,U,P],None,0,0,w,h,0x1908,0x1401,output);assert self.call('glGetError',[],U)==0;return bytes(output)
 def close(self):
  self.current();self.call('glDeleteProgram',[U],None,self.background_program)
  if self.edge_program:self.call('glDeleteProgram',[U],None,self.edge_program)
  if self.hud_program:self.call('glDeleteProgram',[U],None,self.hud_program);self.call('glDeleteTextures',[I,P],None,1,C.byref(self.hudcopy))
  super().close()
