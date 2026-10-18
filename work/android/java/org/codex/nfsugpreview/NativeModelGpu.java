package org.codex.nfsugpreview;
import android.opengl.GLES20;import java.nio.*;
/** Offscreen diagnostic model endpoint only; not wired into FrameView/gameplay. */
final class NativeModelGpu implements AutoCloseable {
 private int program,asset,rows;private final ByteBuffer zeroColors=ByteBuffer.allocateDirect(160*4);
 private static int shader(int kind,String text){int s=GLES20.glCreateShader(kind);GLES20.glShaderSource(s,text);GLES20.glCompileShader(s);int[] ok={0};GLES20.glGetShaderiv(s,GLES20.GL_COMPILE_STATUS,ok,0);if(ok[0]==0){String why=GLES20.glGetShaderInfoLog(s);GLES20.glDeleteShader(s);throw new IllegalStateException(why);}return s;}
 NativeModelGpu(){
  int v=shader(GLES20.GL_VERTEX_SHADER,"attribute vec2 p;attribute vec3 t;varying vec3 uvq;void main(){gl_Position=vec4(p.x/120.0-1.0,1.0-p.y/80.0,0.0,1.0);uvq=t;}");
  int f=shader(GLES20.GL_FRAGMENT_SHADER,"precision highp float;varying vec3 uvq;uniform sampler2D image;uniform sampler2D zeroRows;uniform float height;void main(){vec4 c=texture2D(image,fract(uvq.xy/uvq.z));float row=clamp(floor((height-gl_FragCoord.y)*160.0/height),0.0,159.0);if(c.a<0.5)c=texture2D(zeroRows,vec2(0.5,(row+0.5)/160.0));gl_FragColor=vec4(c.rgb,1.0);}");
  program=GLES20.glCreateProgram();GLES20.glAttachShader(program,v);GLES20.glAttachShader(program,f);GLES20.glBindAttribLocation(program,0,"p");GLES20.glBindAttribLocation(program,1,"t");GLES20.glLinkProgram(program);GLES20.glDeleteShader(v);GLES20.glDeleteShader(f);int[] ok={0};GLES20.glGetProgramiv(program,GLES20.GL_LINK_STATUS,ok,0);if(ok[0]==0)throw new IllegalStateException(GLES20.glGetProgramInfoLog(program));
  int[] textures=new int[2];GLES20.glGenTextures(2,textures,0);asset=textures[0];rows=textures[1];for(int texture:textures){GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,texture);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_MIN_FILTER,GLES20.GL_NEAREST);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_MAG_FILTER,GLES20.GL_NEAREST);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_WRAP_S,GLES20.GL_CLAMP_TO_EDGE);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_WRAP_T,GLES20.GL_CLAMP_TO_EDGE);}
 }
 int draw(NativeSceneSnapshot scene,int modelIndex,int width,int height){
  if(program==0||scene==null||scene.kind!=1||width<1||height<1)throw new IllegalArgumentException("Diagnostic requires a whole owned scene and viewport");
  NativeModelMesh mesh=new NativeModelMesh(NativeModelMesh.model(scene.geometry(0),modelIndex));
  if(mesh.originalIndices()!=null)throw new IllegalArgumentException("Indexed display palette path pending");
  ByteBuffer layer=scene.packedLayers();zeroColors.clear();for(int y=0;y<160;y++){int ref=layer.getShort(20512+(y*25+24)*2)&65535;int color=layer.getShort(28512+ref*4096)&65535;for(int shift:new int[]{0,5,10}){int channel=(color>>shift)&31;zeroColors.put((byte)((channel<<3)|(channel>>2)));}zeroColors.put((byte)255);}zeroColors.position(0);
  GLES20.glViewport(0,0,width,height);GLES20.glDisable(GLES20.GL_DEPTH_TEST);GLES20.glDisable(GLES20.GL_BLEND);GLES20.glDisable(GLES20.GL_CULL_FACE);GLES20.glDisable(GLES20.GL_SCISSOR_TEST);GLES20.glClearColor(0,0,0,1);GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT);if(mesh.triangleVertices==0)return 0;GLES20.glUseProgram(program);GLES20.glPixelStorei(GLES20.GL_UNPACK_ALIGNMENT,1);
  GLES20.glActiveTexture(GLES20.GL_TEXTURE0);GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,asset);GLES20.glTexImage2D(GLES20.GL_TEXTURE_2D,0,GLES20.GL_RGBA,mesh.width,mesh.height,0,GLES20.GL_RGBA,GLES20.GL_UNSIGNED_BYTE,mesh.texture());GLES20.glUniform1i(GLES20.glGetUniformLocation(program,"image"),0);
  GLES20.glActiveTexture(GLES20.GL_TEXTURE1);GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,rows);GLES20.glTexImage2D(GLES20.GL_TEXTURE_2D,0,GLES20.GL_RGBA,1,160,0,GLES20.GL_RGBA,GLES20.GL_UNSIGNED_BYTE,zeroColors);GLES20.glUniform1i(GLES20.glGetUniformLocation(program,"zeroRows"),1);GLES20.glUniform1f(GLES20.glGetUniformLocation(program,"height"),height);
  GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER,0);FloatBuffer vertices=mesh.vertices();vertices.position(0);GLES20.glVertexAttribPointer(0,2,GLES20.GL_FLOAT,false,20,vertices);GLES20.glEnableVertexAttribArray(0);vertices=mesh.vertices();vertices.position(2);GLES20.glVertexAttribPointer(1,3,GLES20.GL_FLOAT,false,20,vertices);GLES20.glEnableVertexAttribArray(1);GLES20.glDrawArrays(GLES20.GL_TRIANGLES,0,mesh.triangleVertices);GLES20.glDisableVertexAttribArray(0);GLES20.glDisableVertexAttribArray(1);
  int error=GLES20.glGetError();if(error!=GLES20.GL_NO_ERROR)throw new IllegalStateException("Model GPU error "+error);return mesh.triangleVertices/3;
 }
 @Override public void close(){if(program!=0){GLES20.glDeleteProgram(program);GLES20.glDeleteTextures(2,new int[]{asset,rows},0);program=asset=rows=0;}}
}
