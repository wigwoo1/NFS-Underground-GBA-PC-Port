package org.codex.nfsugpreview;
/** Owned exact sky+classified geometry+historical OBJ HUD; not a complete background. */
final class NativeRaceSceneGpu implements AutoCloseable {
 private final NativeSkySceneGpu background=new NativeSkySceneGpu();private final NativeHudGpu hud=new NativeHudGpu();
 int draw(NativeSkyScene frame,int targetWidth,int targetHeight,int width,int height){if(frame==null||width<=0||height<=0||targetWidth<width||targetHeight<height)throw new IllegalArgumentException("race scene target");NativeHudFrame prepared=new NativeHudFrame(frame.scene);new NativeSceneComposition(frame.scene);int triangles=background.draw(frame,width,height);hud.draw(prepared,targetWidth,targetHeight,width,height);return triangles;}
 public void close(){hud.close();background.close();}
}
