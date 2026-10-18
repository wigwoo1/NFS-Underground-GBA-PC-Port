from gles_model_reference import GLESModelReference,P,I,U,F,C
import math
class GLESWorldReference(GLESModelReference):
 def render_surface(self,vertices,planes,images,palette,tw,th,indexed,wall,shade,w,h,aw,ah,bounds,top,bottom):
  self.current();self.tex(0,self.textures[2],w,h,None);self.call('glBindFramebuffer',[U,U],None,0x8d40,self.fbo);self.call('glFramebufferTexture2D',[U,U,U,U,I],None,0x8d40,0x8ce0,0xde1,self.textures[2],0);assert self.call('glCheckFramebufferStatus',[U],U,0x8d40)==0x8cd5
  for flag in [0xbe2,0xb71,0xb44,0xc11,0xbd0]:self.call('glDisable',[U],None,flag)
  self.call('glViewport',[I,I,I,I],None,0,0,w,h);self.call('glClearColor',[F,F,F,F],None,0,0,0,0);self.call('glClear',[U],None,0x4000);self.call('glUseProgram',[U],None,self.program);self.call('glPixelStorei',[U,I],None,0xcf5,1);self.tex(1,self.textures[1],256,160,palette)
  for name,value in [('image',0),('zeroRows',1)]:self.call('glUniform1i',[I,I],None,self.uniform(name),value)
  for name,value in [('height',ah),('viewportWidth',aw),('wall',wall),('indexed',indexed)]:self.call('glUniform1f',[I,F],None,self.uniform(name),value)
  self.call('glViewport',[I,I,I,I],None,0,0,aw,ah)
  left,right,btop,bbottom=bounds;left=math.ceil(left*aw/240-.5);right=math.ceil(right*aw/240-.5);t=math.ceil(max(top,btop)*ah/160-.5);b=math.ceil(min(bottom,bbottom)*ah/160-.5)
  if left<right and t<b and vertices:
   self.call('glEnable',[U],None,0xc11);storage=C.create_string_buffer(vertices);self.call('glBindBuffer',[U,U],None,0x8892,0)
   for attr,size,offset in [(0,2,0),(1,3,8)]:self.call('glVertexAttribPointer',[U,I,U,U,I,P],None,attr,size,0x1406,0,20,C.addressof(storage)+offset);self.call('glEnableVertexAttribArray',[U],None,attr)
   start=left
   while start<right:
    level=shade[start] if shade else 0;end=right
    if shade:
     end=start+1
     while end<right and shade[end]==level:end+=1
    self.tex(0,self.textures[0],tw,th,images[level]);self.call('glScissor',[I,I,I,I],None,start,ah-b,end-start,b-t)
    for tri in range(len(planes)//44):
     plane=(F*11).from_buffer_copy(planes[tri*44:(tri+1)*44]);self.call('glUniform2f',[I,F,F],None,self.uniform('origin'),plane[0],plane[1])
     for name,offset in [('planeBase',8),('planeX',20),('planeY',32)]:self.call('glUniform3fv',[I,I,P],None,self.uniform(name),1,C.addressof(plane)+offset)
     self.call('glDrawArrays',[U,I,I],None,4,tri*3,3)
    start=end
  output=(C.c_ubyte*(w*h*4))();self.call('glPixelStorei',[U,I],None,0xd05,1);self.call('glReadPixels',[I,I,I,I,U,U,P],None,0,0,w,h,0x1908,0x1401,output);assert self.call('glGetError',[],U)==0;return bytes(output)
