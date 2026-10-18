package org.codex.nfsugpreview;
import android.opengl.GLES20;import java.nio.*;
/** Source-addressed boundary quads. Caller must bind original command/scene ownership. */
final class NativeRoadEdgeGpu implements AutoCloseable {
 private int program;private final int[] textures=new int[2];
 private static int shader(int kind,String source){int s=GLES20.glCreateShader(kind);GLES20.glShaderSource(s,source);GLES20.glCompileShader(s);int[] ok={0};GLES20.glGetShaderiv(s,GLES20.GL_COMPILE_STATUS,ok,0);if(ok[0]==0)throw new IllegalStateException(GLES20.glGetShaderInfoLog(s));return s;}
 NativeRoadEdgeGpu(){
  int v=shader(GLES20.GL_VERTEX_SHADER,"attribute vec2 p;attribute vec2 uv;varying vec2 t;void main(){gl_Position=vec4(p.x/120.-1.,1.-p.y/80.,0.,1.);t=uv;}"),f=shader(GLES20.GL_FRAGMENT_SHADER,"precision highp float;varying vec2 t;uniform sampler2D indices;uniform sampler2D palette;uniform float height;void main(){float index=floor(texture2D(indices,t).r*255.+.5);float row=clamp(floor((height-gl_FragCoord.y)*160./height),0.,159.);gl_FragColor=vec4(texture2D(palette,vec2((index+.5)/256.,(row+.5)/160.)).rgb,1.);}");
  program=GLES20.glCreateProgram();GLES20.glAttachShader(program,v);GLES20.glAttachShader(program,f);GLES20.glBindAttribLocation(program,0,"p");GLES20.glBindAttribLocation(program,1,"uv");GLES20.glLinkProgram(program);GLES20.glDeleteShader(v);GLES20.glDeleteShader(f);int[] ok={0};GLES20.glGetProgramiv(program,GLES20.GL_LINK_STATUS,ok,0);if(ok[0]==0)throw new IllegalStateException(GLES20.glGetProgramInfoLog(program));GLES20.glGenTextures(2,textures,0);
 }
 int draw(NativeRoadAsset asset,NativeRoadEdgePlan plan,NativeSceneSnapshot scene,int width,int height,int top,int bottom){
  if(program==0||asset==null||plan==null||!plan.belongsTo(asset)||scene==null||width<1||height<1||width>16384||height>16384||top<0||bottom>160||top>bottom)throw new IllegalArgumentException("Road edge target");
  return drawRecords(asset.texture(),plan.records(),scene,width,height,top,bottom);
 }
 int drawRetention(NativeRoadRetention retention,NativeSceneSnapshot scene,int width,int height){
  if(program==0||retention==null||!retention.belongsTo(scene)||width<1||height<1||width>16384||height>16384)throw new IllegalArgumentException("Retained road target");int cells=0;
  for(int i=0;i<retention.count();i++){NativeRoadRetention.Draw draw=retention.draw(i);cells+=drawRecords(retention.texture(draw),draw.records(),scene,width,height,draw.top,draw.bottom);}return cells;
 }
 int drawWallRetention(NativeWallRetention retention,NativeSceneSnapshot scene,int width,int height){
  if(program==0||retention==null||!retention.belongsTo(scene)||width<1||height<1||width>16384||height>16384)throw new IllegalArgumentException("Retained wall target");int cells=0;
  for(int i=0;i<retention.count();i++){NativeWallRetention.Draw draw=retention.draw(i);cells+=drawRecords(retention.texture(draw),draw.records(),scene,width,height,draw.top,draw.bottom);}return cells;
 }
 private int drawRecords(ByteBuffer source,int[] records,NativeSceneSnapshot scene,int width,int height,int top,int bottom){
  if(records.length==0||top==bottom)return 0;int tw=1024,th=(source.remaining()+tw-1)/tw;ByteBuffer indexed=ByteBuffer.allocateDirect(tw*th*4);for(int i=0;i<source.remaining();i++){indexed.put(i*4,source.get(i));indexed.put(i*4+3,(byte)255);}ByteBuffer palette=NativeHistoricalPalette.rgba(scene);
  FloatBuffer vertices=ByteBuffer.allocateDirect(records.length*32).order(ByteOrder.nativeOrder()).asFloatBuffer();int count=0;int[] corners={0,0,1,0,0,1,0,1,1,0,1,1};
  for(int i=0;i<records.length;i+=3){int x=records[i],y=records[i+1],offset=records[i+2];if(y<top||y>=bottom)continue;if(offset<0||offset>=source.remaining())throw new IllegalArgumentException("Road texture offset");float u=(offset%tw+.5f)/tw,v=(offset/tw+.5f)/th;for(int c=0;c<12;c+=2)vertices.put(new float[]{x+corners[c],y+corners[c+1],u,v});count++;}vertices.flip();if(count==0)return 0;
  GLES20.glUseProgram(program);GLES20.glPixelStorei(GLES20.GL_UNPACK_ALIGNMENT,1);
  for(int i=0;i<2;i++){GLES20.glActiveTexture(GLES20.GL_TEXTURE0+i);GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,textures[i]);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_MIN_FILTER,GLES20.GL_NEAREST);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_MAG_FILTER,GLES20.GL_NEAREST);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_WRAP_S,GLES20.GL_CLAMP_TO_EDGE);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_WRAP_T,GLES20.GL_CLAMP_TO_EDGE);GLES20.glTexImage2D(GLES20.GL_TEXTURE_2D,0,GLES20.GL_RGBA,i==0?tw:256,i==0?th:160,0,GLES20.GL_RGBA,GLES20.GL_UNSIGNED_BYTE,i==0?indexed:palette);}
  GLES20.glUniform1i(GLES20.glGetUniformLocation(program,"indices"),0);GLES20.glUniform1i(GLES20.glGetUniformLocation(program,"palette"),1);GLES20.glUniform1f(GLES20.glGetUniformLocation(program,"height"),height);GLES20.glViewport(0,0,width,height);GLES20.glDisable(GLES20.GL_SCISSOR_TEST);GLES20.glDisable(GLES20.GL_DEPTH_TEST);GLES20.glDisable(GLES20.GL_BLEND);GLES20.glDisable(GLES20.GL_CULL_FACE);GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER,0);vertices.position(0);GLES20.glVertexAttribPointer(0,2,GLES20.GL_FLOAT,false,16,vertices);vertices.position(2);GLES20.glVertexAttribPointer(1,2,GLES20.GL_FLOAT,false,16,vertices);GLES20.glEnableVertexAttribArray(0);GLES20.glEnableVertexAttribArray(1);GLES20.glDrawArrays(GLES20.GL_TRIANGLES,0,count*6);GLES20.glDisableVertexAttribArray(0);GLES20.glDisableVertexAttribArray(1);if(GLES20.glGetError()!=GLES20.GL_NO_ERROR)throw new IllegalStateException("Road edge GPU");return count;
 }
 public void close(){if(program!=0){GLES20.glDeleteProgram(program);GLES20.glDeleteTextures(2,textures,0);program=0;}}
}
