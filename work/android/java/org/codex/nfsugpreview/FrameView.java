package org.codex.nfsugpreview;

import android.content.Context;

import android.opengl.*;

import java.nio.*;

import javax.microedition.khronos.egl.EGLConfig;

import javax.microedition.khronos.opengles.GL10;

final class FrameView extends GLSurfaceView implements GLSurfaceView.Renderer {

 private final GameSession session;

 private final FloatBuffer vertices=ByteBuffer.allocateDirect(16*4).order(ByteOrder.nativeOrder()).asFloatBuffer();

 private final ByteBuffer upload=ByteBuffer.allocateDirect(NativeCore.FRAME_BYTES);

 private byte[] last;

 private int program,texture,vbo,width,height;
 private NativeLiveGpu live;
 volatile long nativeFramesRendered,originalFramesRendered,supersededFramesRendered,uniqueNativeFramesRendered;
 private NativePresentation.Frame lastNativePresented;
 interface Probe {void drawn(NativePresentation.Frame nativeFrame,int x,int y,int width,int height);}
 volatile Probe probe;

 FrameView(Context context,GameSession session){super(context);this.session=session;setEGLContextClientVersion(2);setPreserveEGLContextOnPause(true);setRenderer(this);}

 private int shader(int type,String source){

  int s=GLES20.glCreateShader(type);GLES20.glShaderSource(s,source);GLES20.glCompileShader(s);

  int[] ok=new int[1];GLES20.glGetShaderiv(s,GLES20.GL_COMPILE_STATUS,ok,0);if(ok[0]==0)throw new IllegalStateException(GLES20.glGetShaderInfoLog(s));return s;

 }

 public void onSurfaceCreated(GL10 unused,EGLConfig config){

  int v=shader(GLES20.GL_VERTEX_SHADER,"attribute vec2 p;attribute vec2 t;varying vec2 uv;void main(){gl_Position=vec4(p,0,1);uv=t;}");

  int f=shader(GLES20.GL_FRAGMENT_SHADER,"precision mediump float;varying vec2 uv;uniform sampler2D image;uniform float flip;void main(){gl_FragColor=texture2D(image,vec2(uv.x,mix(uv.y,1.0-uv.y,flip)));}");

  program=GLES20.glCreateProgram();GLES20.glAttachShader(program,v);GLES20.glAttachShader(program,f);GLES20.glBindAttribLocation(program,0,"p");GLES20.glBindAttribLocation(program,1,"t");GLES20.glLinkProgram(program);

  int[] linked=new int[1];GLES20.glGetProgramiv(program,GLES20.GL_LINK_STATUS,linked,0);if(linked[0]==0)throw new IllegalStateException("GPU program link failed");

  GLES20.glDeleteShader(v);GLES20.glDeleteShader(f);

  int[] names=new int[1];GLES20.glGenTextures(1,names,0);texture=names[0];GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,texture);

  GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_MIN_FILTER,GLES20.GL_NEAREST);

  GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_MAG_FILTER,GLES20.GL_NEAREST);

  GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_WRAP_S,GLES20.GL_CLAMP_TO_EDGE);

  GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_WRAP_T,GLES20.GL_CLAMP_TO_EDGE);

  GLES20.glTexImage2D(GLES20.GL_TEXTURE_2D,0,GLES20.GL_RGBA,240,160,0,GLES20.GL_RGBA,GLES20.GL_UNSIGNED_BYTE,null);

  vertices.put(new float[]{-1,-1,0,1,1,-1,1,1,-1,1,0,0,1,1,1,0}).position(0);

  GLES20.glGenBuffers(1,names,0);vbo=names[0];GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER,vbo);

  GLES20.glBufferData(GLES20.GL_ARRAY_BUFFER,64,vertices,GLES20.GL_STATIC_DRAW);last=null;live=null;lastNativePresented=null;

 }

 public void onSurfaceChanged(GL10 unused,int w,int h){width=w;height=h;}

 public void onDrawFrame(GL10 unused){

  GLES20.glViewport(0,0,width,height);GLES20.glClearColor(0,0,0,1);GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT);

  byte[] current=session.frame;if(current==null||width<=0||height<=0)return;
  int w=Math.min(width,(int)(height*1.5));int h=(int)(w/1.5);if(w<=0||h<=0)return;
  int nativeTexture=0;NativePresentation.Frame pending=session.presentation.latest();
  if(pending!=null&&pending.scene!=null){try{if(live==null){long initStart=session.profile.start();live=new NativeLiveGpu(session.profile);session.profile.end(NativeWorkProfile.INIT,initStart);}long drawStart=session.profile.start();int rendered=live.draw(pending.scene,w,h);session.profile.end(NativeWorkProfile.DRAW,drawStart);if(session.presentation.canPresent(pending)){nativeTexture=rendered;if(!session.presentation.current(pending))supersededFramesRendered++;}}catch(RuntimeException failure){if(live!=null){live.close();live=null;}session.nativeRenderFailed(failure);}}
  GLES20.glDisable(GLES20.GL_BLEND);GLES20.glDisable(GLES20.GL_DEPTH_TEST);GLES20.glDisable(GLES20.GL_CULL_FACE);GLES20.glDisable(GLES20.GL_SCISSOR_TEST);GLES20.glColorMask(true,true,true,true);
  GLES20.glViewport(0,0,width,height);GLES20.glClearColor(0,0,0,1);GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT);

  GLES20.glUseProgram(program);GLES20.glActiveTexture(GLES20.GL_TEXTURE0);GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,nativeTexture==0?texture:nativeTexture);
  GLES20.glUniform1i(GLES20.glGetUniformLocation(program,"image"),0);GLES20.glUniform1f(GLES20.glGetUniformLocation(program,"flip"),nativeTexture==0?0:1);

  if(nativeTexture==0&&current!=last){upload.clear();upload.put(current);upload.position(0);GLES20.glTexSubImage2D(GLES20.GL_TEXTURE_2D,0,0,0,240,160,GLES20.GL_RGBA,GLES20.GL_UNSIGNED_BYTE,upload);last=current;}

  GLES20.glViewport((width-w)/2,(height-h)/2,w,h);

  GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER,vbo);GLES20.glVertexAttribPointer(0,2,GLES20.GL_FLOAT,false,16,0);GLES20.glEnableVertexAttribArray(0);

  GLES20.glVertexAttribPointer(1,2,GLES20.GL_FLOAT,false,16,8);GLES20.glEnableVertexAttribArray(1);

  GLES20.glDrawArrays(GLES20.GL_TRIANGLE_STRIP,0,4);
  if(nativeTexture!=0){nativeFramesRendered++;if(pending!=lastNativePresented){uniqueNativeFramesRendered++;lastNativePresented=pending;}}else originalFramesRendered++;
  Probe callback=probe;if(callback!=null)callback.drawn(nativeTexture!=0?pending:null,(width-w)/2,(height-h)/2,w,h);

 }

}

