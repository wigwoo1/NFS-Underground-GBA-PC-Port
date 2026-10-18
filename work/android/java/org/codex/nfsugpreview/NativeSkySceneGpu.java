package org.codex.nfsugpreview;
import android.opengl.GLES20;import java.nio.*;
/** Exact captured sky footprint behind native geometry. HUD/initial fill are separate. */
final class NativeSkySceneGpu implements AutoCloseable {
 private final NativeRgbaGpu sky=new NativeRgbaGpu();private final NativeSceneGpu geometry=new NativeSceneGpu();
 int draw(NativeSkyScene frame,int width,int height){if(frame==null||width<=0||height<=0)throw new IllegalArgumentException("sky scene target");new NativeSceneComposition(frame.scene);ByteBuffer rgba=frame.exactRgba();GLES20.glDisable(GLES20.GL_SCISSOR_TEST);GLES20.glColorMask(true,true,true,true);GLES20.glClearColor(0,0,0,1);GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT);sky.draw(rgba,width,height);return geometry.drawOverBackground(frame.scene,width,height);}
 public void close(){geometry.close();sky.close();}
}
