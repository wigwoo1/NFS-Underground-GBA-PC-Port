package org.codex.nfsugpreview;
import android.opengl.GLES20;
/** Origin-zero offscreen composition, then FrameView letterboxes the returned texture. */
final class NativeLiveGpu implements AutoCloseable {
 private final NativeBackgroundSceneGpu renderer=new NativeBackgroundSceneGpu();
 private int texture,framebuffer,width,height;
 private NativeRetainedScene renderedScene;
 NativeLiveGpu(NativeWorkProfile profile){renderer.profile=profile;}
 int draw(NativeRetainedScene scene,int w,int h){
  if(scene==null||w<=0||h<=0)throw new IllegalArgumentException("Live target");
  try{
   if(texture==0||width!=w||height!=h){releaseTarget();int[] n={0};GLES20.glGenTextures(1,n,0);texture=n[0];GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,texture);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_MIN_FILTER,GLES20.GL_NEAREST);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_MAG_FILTER,GLES20.GL_NEAREST);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_WRAP_S,GLES20.GL_CLAMP_TO_EDGE);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_WRAP_T,GLES20.GL_CLAMP_TO_EDGE);GLES20.glTexImage2D(GLES20.GL_TEXTURE_2D,0,GLES20.GL_RGBA,w,h,0,GLES20.GL_RGBA,GLES20.GL_UNSIGNED_BYTE,null);GLES20.glGenFramebuffers(1,n,0);framebuffer=n[0];GLES20.glBindFramebuffer(GLES20.GL_FRAMEBUFFER,framebuffer);GLES20.glFramebufferTexture2D(GLES20.GL_FRAMEBUFFER,GLES20.GL_COLOR_ATTACHMENT0,GLES20.GL_TEXTURE_2D,texture,0);if(GLES20.glCheckFramebufferStatus(GLES20.GL_FRAMEBUFFER)!=GLES20.GL_FRAMEBUFFER_COMPLETE)throw new IllegalStateException("Live framebuffer incomplete");width=w;height=h;}
   // Immutable scene identity and unchanged target are the only reuse key.
   // Invalidate before drawing: a failed draw may have partially overwritten the image.
   if(renderedScene==scene)return texture;
   renderedScene=null;
   GLES20.glBindFramebuffer(GLES20.GL_FRAMEBUFFER,framebuffer);renderer.drawRetained(scene,w,h,w,h);if(GLES20.glGetError()!=GLES20.GL_NO_ERROR)throw new IllegalStateException("Live GPU draw failed");renderedScene=scene;return texture;
  }finally{GLES20.glBindFramebuffer(GLES20.GL_FRAMEBUFFER,0);}
 }
 private void releaseTarget(){renderedScene=null;if(framebuffer!=0)GLES20.glDeleteFramebuffers(1,new int[]{framebuffer},0);if(texture!=0)GLES20.glDeleteTextures(1,new int[]{texture},0);framebuffer=texture=width=height=0;}
 public void close(){renderer.close();releaseTarget();}
}
