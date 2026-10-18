package org.codex.nfsugpreview;
import android.opengl.GLES20;import java.nio.*;
/** Ordered source world/model endpoints with retained whole/split ownership. */
final class NativeSceneGpu implements AutoCloseable {
 private int program,asset,rows;private ByteBuffer paletteColors;
 private static int shader(int kind,String text){int s=GLES20.glCreateShader(kind);GLES20.glShaderSource(s,text);GLES20.glCompileShader(s);int[] ok={0};GLES20.glGetShaderiv(s,GLES20.GL_COMPILE_STATUS,ok,0);if(ok[0]==0){String why=GLES20.glGetShaderInfoLog(s);GLES20.glDeleteShader(s);throw new IllegalStateException(why);}return s;}
 NativeSceneGpu(){
  int v=shader(GLES20.GL_VERTEX_SHADER,"attribute vec2 p;attribute vec3 t;varying vec3 uvq;void main(){gl_Position=vec4(p.x/120.0-1.0,1.0-p.y/80.0,0.0,1.0);uvq=t;}");
  int f=shader(GLES20.GL_FRAGMENT_SHADER,"precision highp float;uniform vec2 origin;uniform vec3 planeBase;uniform vec3 planeX;uniform vec3 planeY;uniform float viewportWidth;uniform sampler2D image;uniform sampler2D zeroRows;uniform float height;uniform float wall;uniform float indexed;void main(){vec2 delta=vec2(gl_FragCoord.x*240.0/viewportWidth,(height-gl_FragCoord.y)*160.0/height)-origin;vec3 uvq=planeBase+planeX*delta.x+planeY*delta.y;vec4 c=texture2D(image,fract(uvq.xy/uvq.z));float row=clamp(floor((height-gl_FragCoord.y)*160.0/height),0.0,159.0);if(wall>0.5&&c.a<0.25)discard;if(indexed>0.5)c=texture2D(zeroRows,vec2((floor(c.r*255.0+0.5)+0.5)/256.0,(row+0.5)/160.0));else if(c.a<(wall>0.5?0.75:0.5))c=texture2D(zeroRows,vec2(0.5/256.0,(row+0.5)/160.0));gl_FragColor=vec4(c.rgb,1.0);}");
  program=GLES20.glCreateProgram();GLES20.glAttachShader(program,v);GLES20.glAttachShader(program,f);GLES20.glBindAttribLocation(program,0,"p");GLES20.glBindAttribLocation(program,1,"t");GLES20.glLinkProgram(program);GLES20.glDeleteShader(v);GLES20.glDeleteShader(f);int[] ok={0};GLES20.glGetProgramiv(program,GLES20.GL_LINK_STATUS,ok,0);if(ok[0]==0)throw new IllegalStateException(GLES20.glGetProgramInfoLog(program));
  int[] textures=new int[2];GLES20.glGenTextures(2,textures,0);asset=textures[0];rows=textures[1];for(int texture:textures){GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,texture);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_MIN_FILTER,GLES20.GL_NEAREST);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_MAG_FILTER,GLES20.GL_NEAREST);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_WRAP_S,GLES20.GL_CLAMP_TO_EDGE);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_WRAP_T,GLES20.GL_CLAMP_TO_EDGE);}
 }
 interface Observer { void afterDraw(int command); }
 int draw(NativeSceneSnapshot scene,int width,int height){return draw(scene,width,height,null);}
 int draw(NativeSceneSnapshot scene,int width,int height,Observer observer){return draw(scene,width,height,observer,true);}
 int drawOverBackground(NativeSceneSnapshot scene,int width,int height,Observer observer){return draw(scene,width,height,observer,false);}
 int drawOverBackground(NativeSceneSnapshot scene,int width,int height){return draw(scene,width,height,null,false);}
 int drawOverBackground(NativeSceneSnapshot scene,int width,int height,NativeRoadBindings bindings,NativeRoadEdgeGpu edge){if(bindings==null||!bindings.belongsTo(scene)||edge==null)throw new IllegalArgumentException("Road scene binding");return draw(scene,width,height,null,false,bindings,edge);}
 private int draw(NativeSceneSnapshot scene,int width,int height,Observer observer,boolean clear){return draw(scene,width,height,observer,clear,null,null);}
 int drawPrepared(NativePreparedScene prepared,int width,int height,NativeRoadBindings bindings,NativeRoadEdgeGpu edge){if(prepared==null||(bindings!=null&&(!bindings.belongsTo(prepared.scene)||edge==null)))throw new IllegalArgumentException("Prepared scene ownership");return draw(prepared.scene,width,height,null,false,bindings,edge,prepared.composition,prepared.paletteRgba());}
 private int draw(NativeSceneSnapshot scene,int width,int height,Observer observer,boolean clear,NativeRoadBindings bindings,NativeRoadEdgeGpu edge){
  return draw(scene,width,height,observer,clear,bindings,edge,null,null);
 }
 private int draw(NativeSceneSnapshot scene,int width,int height,Observer observer,boolean clear,NativeRoadBindings bindings,NativeRoadEdgeGpu edge,NativeSceneComposition prepared,ByteBuffer palette){
  if(program==0||scene==null||width<1||height<1)throw new IllegalArgumentException("Owned scene required");
  NativeSceneComposition composition=prepared==null?new NativeSceneComposition(scene):prepared;if(!composition.belongsTo(scene))throw new IllegalArgumentException("Prepared geometry ownership");
  paletteColors=palette==null?NativeHistoricalPalette.rgba(scene):palette;
  GLES20.glViewport(0,0,width,height);GLES20.glDisable(GLES20.GL_DEPTH_TEST);GLES20.glDisable(GLES20.GL_BLEND);GLES20.glDisable(GLES20.GL_CULL_FACE);GLES20.glDisable(GLES20.GL_SCISSOR_TEST);if(clear){GLES20.glClearColor(0,0,0,1);GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT);}GLES20.glUseProgram(program);GLES20.glPixelStorei(GLES20.GL_UNPACK_ALIGNMENT,1);
  GLES20.glActiveTexture(GLES20.GL_TEXTURE1);GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,rows);GLES20.glTexImage2D(GLES20.GL_TEXTURE_2D,0,GLES20.GL_RGBA,256,160,0,GLES20.GL_RGBA,GLES20.GL_UNSIGNED_BYTE,paletteColors);GLES20.glUniform1i(GLES20.glGetUniformLocation(program,"zeroRows"),1);GLES20.glUniform1f(GLES20.glGetUniformLocation(program,"height"),height);GLES20.glUniform1f(GLES20.glGetUniformLocation(program,"viewportWidth"),width);
  int triangles=0,commandBase=0;
  for(int owner=0;owner<composition.count();owner++){NativeSceneDrawPlan plan=composition.plan(owner);for(int i=0;i<plan.count();i++){
   NativeSceneDrawPlan.Draw mesh=plan.draw(i);if(mesh.vertices==0)continue;int[] clip=composition.clip(owner,mesh.bounds).scissor(width,height);if(clip[2]==0||clip[3]==0)continue;GLES20.glEnable(GLES20.GL_SCISSOR_TEST);
   if(mesh.lighting==null){GLES20.glScissor(clip[0],clip[1],clip[2],clip[3]);submit(mesh,mesh.image());}
   else{int[] shade=mesh.lighting.curve.columns(width);int start=clip[0],right=start+clip[2];while(start<right){int end=start+1,level=shade[start];while(end<right&&shade[end]==level)end++;GLES20.glScissor(start,clip[1],end-start,clip[3]);submit(mesh,mesh.lighting.variant(level));start=end;}}
   if(bindings!=null)for(int binding=0;binding<bindings.count();binding++){NativeRoadBindings.Binding b=bindings.binding(binding);if(!b.empty&&b.owner==owner&&b.command==i){edge.draw(b.asset,b.plan,scene,width,height,b.top,b.bottom);GLES20.glUseProgram(program);GLES20.glActiveTexture(GLES20.GL_TEXTURE1);GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,rows);}}
   triangles+=mesh.vertices/3;if(observer!=null)observer.afterDraw(commandBase+i);
  }
  commandBase+=plan.count();}
  GLES20.glDisable(GLES20.GL_SCISSOR_TEST);int error=GLES20.glGetError();if(error!=GLES20.GL_NO_ERROR)throw new IllegalStateException("Scene GPU error "+error);return triangles;
 }
 private void submit(NativeSceneDrawPlan.Draw mesh,ByteBuffer image){
  GLES20.glUniform1f(GLES20.glGetUniformLocation(program,"wall"),mesh.wall?1:0);GLES20.glUniform1f(GLES20.glGetUniformLocation(program,"indexed"),mesh.indexed?1:0);
  GLES20.glActiveTexture(GLES20.GL_TEXTURE0);GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,asset);GLES20.glTexImage2D(GLES20.GL_TEXTURE_2D,0,GLES20.GL_RGBA,mesh.width,mesh.height,0,GLES20.GL_RGBA,GLES20.GL_UNSIGNED_BYTE,image);GLES20.glUniform1i(GLES20.glGetUniformLocation(program,"image"),0);
  GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER,0);FloatBuffer vertices=mesh.mesh();vertices.position(0);GLES20.glVertexAttribPointer(0,2,GLES20.GL_FLOAT,false,20,vertices);GLES20.glEnableVertexAttribArray(0);vertices=mesh.mesh();vertices.position(2);GLES20.glVertexAttribPointer(1,3,GLES20.GL_FLOAT,false,20,vertices);GLES20.glEnableVertexAttribArray(1);
  for(int vertex=0;vertex<mesh.vertices;vertex+=3){NativeTexturePlane plane=new NativeTexturePlane(mesh.mesh(),vertex,mesh.model);GLES20.glUniform2f(GLES20.glGetUniformLocation(program,"origin"),plane.x,plane.y);GLES20.glUniform3fv(GLES20.glGetUniformLocation(program,"planeBase"),1,plane.base,0);GLES20.glUniform3fv(GLES20.glGetUniformLocation(program,"planeX"),1,plane.dx,0);GLES20.glUniform3fv(GLES20.glGetUniformLocation(program,"planeY"),1,plane.dy,0);GLES20.glDrawArrays(GLES20.GL_TRIANGLES,vertex,3);}GLES20.glDisableVertexAttribArray(0);GLES20.glDisableVertexAttribArray(1);
 }
 @Override public void close(){if(program!=0){GLES20.glDeleteProgram(program);GLES20.glDeleteTextures(2,new int[]{asset,rows},0);program=asset=rows=0;}}
}
