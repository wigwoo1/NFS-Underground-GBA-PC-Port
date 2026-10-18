package org.codex.nfsugpreview;
import android.opengl.GLES20;import java.nio.ByteBuffer;
/** Captured initial background, native geometry and historical OBJ HUD.
 * Diagnostic endpoint composition; completeness and live pacing require separate gates.
 */
final class NativeBackgroundSceneGpu implements AutoCloseable {
 NativeWorkProfile profile;
 private long start(){return profile==null?0:profile.start();}
 private void end(int stage,long time){if(profile!=null)profile.end(stage,time);}
 private final NativeRgbaGpu background=new NativeRgbaGpu();
 private final NativeSceneGpu geometry=new NativeSceneGpu();
 private final NativeRoadEdgeGpu edge=new NativeRoadEdgeGpu();
 private final NativeHudGpu hud=new NativeHudGpu();
 int drawRetained(NativeRetainedScene frame,int targetWidth,int targetHeight,int width,int height){if(frame==null)throw new IllegalArgumentException("Retained scene required");return draw(frame.background,targetWidth,targetHeight,width,height,null,frame.roads,frame.walls,frame.prepared);}
 int draw(NativeBackgroundScene frame,int targetWidth,int targetHeight,int width,int height){return draw(frame,targetWidth,targetHeight,width,height,null);}
 int draw(NativeBackgroundScene frame,int targetWidth,int targetHeight,int width,int height,NativeRoadBindings bindings){return draw(frame,targetWidth,targetHeight,width,height,bindings,null);}
 int draw(NativeBackgroundScene frame,int targetWidth,int targetHeight,int width,int height,NativeRoadBindings bindings,NativeRoadRetention retention){return draw(frame,targetWidth,targetHeight,width,height,bindings,retention,null);}
 int draw(NativeBackgroundScene frame,int targetWidth,int targetHeight,int width,int height,NativeRoadBindings bindings,NativeRoadRetention retention,NativeWallRetention walls){
  return draw(frame,targetWidth,targetHeight,width,height,bindings,retention,walls,null);
 }
 private int draw(NativeBackgroundScene frame,int targetWidth,int targetHeight,int width,int height,NativeRoadBindings bindings,NativeRoadRetention retention,NativeWallRetention walls,NativePreparedScene cached){
  if(frame==null||width<=0||height<=0||targetWidth<width||targetHeight<height)throw new IllegalArgumentException("background scene target");
  // Validate every component before changing framebuffer state.
  long stageStart=start();NativeSceneSnapshot scene=frame.sky.scene;
  if(bindings!=null&&!bindings.belongsTo(scene))throw new IllegalArgumentException("Road scene ownership");
  if(retention!=null&&!retention.belongsTo(scene))throw new IllegalArgumentException("Retained road scene ownership");
  if(walls!=null&&!walls.belongsTo(scene))throw new IllegalArgumentException("Retained wall scene ownership");
  if(cached!=null&&cached.background!=frame)throw new IllegalArgumentException("Prepared background ownership");
  NativePreparedScene prepared=cached==null?new NativePreparedScene(frame):cached;
  ByteBuffer rgba=prepared.backgroundRgba();
  end(NativeWorkProfile.PREPARE,stageStart);stageStart=start();
  GLES20.glDisable(GLES20.GL_SCISSOR_TEST);
  GLES20.glColorMask(true,true,true,true);
  GLES20.glClearColor(0,0,0,1);
  GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT);
  background.draw(rgba,width,height);end(NativeWorkProfile.BACKGROUND,stageStart);stageStart=start();
  if(retention!=null)edge.drawRetention(retention,scene,width,height);
  end(NativeWorkProfile.ROAD,stageStart);stageStart=start();
  if(walls!=null)edge.drawWallRetention(walls,scene,width,height);
  end(NativeWorkProfile.WALL,stageStart);stageStart=start();
  int triangles=geometry.drawPrepared(prepared,width,height,bindings,edge);
  end(NativeWorkProfile.WORLD,stageStart);stageStart=start();
  hud.draw(prepared.hud,targetWidth,targetHeight,width,height);end(NativeWorkProfile.HUD,stageStart);
  return triangles;
 }
 public void close(){hud.close();edge.close();geometry.close();background.close();}
}

