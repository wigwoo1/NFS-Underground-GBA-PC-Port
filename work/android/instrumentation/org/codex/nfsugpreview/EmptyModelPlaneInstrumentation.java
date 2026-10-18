package org.codex.nfsugpreview;
import android.app.*;import android.os.*;import android.opengl.*;
import java.io.*;import java.nio.*;import java.lang.reflect.*;import org.json.*;
/** Actual native scene shader/program, synthetic triangle coverage only. No game/core. */
public final class EmptyModelPlaneInstrumentation extends SceneGpuInstrumentation {
 private final ByteBuffer pixels=ByteBuffer.allocateDirect(3840*2160*4);
 private int field(NativeSceneGpu gpu,String name)throws Exception{Field f=NativeSceneGpu.class.getDeclaredField(name);f.setAccessible(true);return f.getInt(gpu);}
 private FloatBuffer triangle(float[] xy){FloatBuffer v=ByteBuffer.allocateDirect(60).order(ByteOrder.nativeOrder()).asFloatBuffer();for(int i=0;i<3;i++)v.put(xy[i*2]).put(xy[i*2+1]).put(i==0?0:1).put(i==2?1:0).put(1);v.position(0);return v.asReadOnlyBuffer();}
 private JSONObject draw(String label,float[] xy,int width,int height,int activeWidth,boolean empty)throws Exception{
  FloatBuffer v=triangle(xy);NativeTexturePlane plane=new NativeTexturePlane(v,0,true);
  if(empty){try{new NativeTexturePlane(v,0);throw new AssertionError("Strict world plane accepted "+label);}catch(IllegalArgumentException expected){}}
  int[] name={0};GLES20.glActiveTexture(GLES20.GL_TEXTURE0);GLES20.glGenTextures(1,name,0);int texture=name[0];GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,texture);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_MIN_FILTER,GLES20.GL_NEAREST);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_MAG_FILTER,GLES20.GL_NEAREST);GLES20.glTexImage2D(GLES20.GL_TEXTURE_2D,0,GLES20.GL_RGBA,width,height,0,GLES20.GL_RGBA,GLES20.GL_UNSIGNED_BYTE,null);GLES20.glGenFramebuffers(1,name,0);int fbo=name[0];GLES20.glBindFramebuffer(GLES20.GL_FRAMEBUFFER,fbo);GLES20.glFramebufferTexture2D(GLES20.GL_FRAMEBUFFER,GLES20.GL_COLOR_ATTACHMENT0,GLES20.GL_TEXTURE_2D,texture,0);ok(GLES20.glCheckFramebufferStatus(GLES20.GL_FRAMEBUFFER)==GLES20.GL_FRAMEBUFFER_COMPLETE,"Coverage framebuffer");
  try(NativeSceneGpu gpu=new NativeSceneGpu()){
   int program=field(gpu,"program");GLES20.glUseProgram(program);
   GLES20.glDisable(GLES20.GL_SCISSOR_TEST);GLES20.glDisable(GLES20.GL_DEPTH_TEST);GLES20.glDisable(GLES20.GL_BLEND);GLES20.glDisable(GLES20.GL_CULL_FACE);GLES20.glViewport(0,0,activeWidth,height);GLES20.glClearColor(0,0,0,1);GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT);
   ByteBuffer red=ByteBuffer.allocateDirect(4);red.put(new byte[]{(byte)255,0,0,(byte)255}).position(0);
   GLES20.glActiveTexture(GLES20.GL_TEXTURE0);GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,field(gpu,"asset"));GLES20.glTexImage2D(GLES20.GL_TEXTURE_2D,0,GLES20.GL_RGBA,1,1,0,GLES20.GL_RGBA,GLES20.GL_UNSIGNED_BYTE,red);GLES20.glUniform1i(GLES20.glGetUniformLocation(program,"image"),0);
   GLES20.glActiveTexture(GLES20.GL_TEXTURE1);GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,field(gpu,"rows"));GLES20.glTexImage2D(GLES20.GL_TEXTURE_2D,0,GLES20.GL_RGBA,1,1,0,GLES20.GL_RGBA,GLES20.GL_UNSIGNED_BYTE,red);GLES20.glUniform1i(GLES20.glGetUniformLocation(program,"zeroRows"),1);
   GLES20.glUniform2f(GLES20.glGetUniformLocation(program,"origin"),plane.x,plane.y);GLES20.glUniform3fv(GLES20.glGetUniformLocation(program,"planeBase"),1,plane.base,0);GLES20.glUniform3fv(GLES20.glGetUniformLocation(program,"planeX"),1,plane.dx,0);GLES20.glUniform3fv(GLES20.glGetUniformLocation(program,"planeY"),1,plane.dy,0);GLES20.glUniform1f(GLES20.glGetUniformLocation(program,"viewportWidth"),activeWidth);GLES20.glUniform1f(GLES20.glGetUniformLocation(program,"height"),height);GLES20.glUniform1f(GLES20.glGetUniformLocation(program,"wall"),0);GLES20.glUniform1f(GLES20.glGetUniformLocation(program,"indexed"),0);
   GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER,0);v.position(0);GLES20.glVertexAttribPointer(0,2,GLES20.GL_FLOAT,false,20,v);GLES20.glEnableVertexAttribArray(0);v.position(2);GLES20.glVertexAttribPointer(1,3,GLES20.GL_FLOAT,false,20,v);GLES20.glEnableVertexAttribArray(1);GLES20.glDrawArrays(GLES20.GL_TRIANGLES,0,3);GLES20.glDisableVertexAttribArray(0);GLES20.glDisableVertexAttribArray(1);
   pixels.clear();pixels.limit(width*height*4);GLES20.glReadPixels(0,0,width,height,GLES20.GL_RGBA,GLES20.GL_UNSIGNED_BYTE,pixels);ok(GLES20.glGetError()==GLES20.GL_NO_ERROR,"Coverage draw/readback "+label);
   int redPixels=0;for(int i=0;i<width*height;i++){int at=i*4,r=pixels.get(at)&255,g=pixels.get(at+1)&255,b=pixels.get(at+2)&255,a=pixels.get(at+3)&255;ok(g==0&&b==0&&(r==0||r==255)&&a==255,"Unexpected coverage color");if(r==255)redPixels++;}
   ok(empty?redPixels==0:redPixels>0,"Coverage mismatch "+label+" "+redPixels);
   JSONObject item=new JSONObject();item.put("case",label);item.put("width",width);item.put("height",height);item.put("active_width",activeWidth);item.put("red_pixels",redPixels);item.put("sha256",digest(pixels));return item;
  }finally{GLES20.glBindFramebuffer(GLES20.GL_FRAMEBUFFER,0);GLES20.glDeleteFramebuffers(1,new int[]{fbo},0);GLES20.glDeleteTextures(1,new int[]{texture},0);}
 }
 private byte[] component(String prefix,int owner,int kind)throws Exception{return java.nio.file.Files.readAllBytes(new File(getTargetContext().getFilesDir(),prefix+"-owner"+owner+"-kind"+kind+".bin").toPath());}
 private NativeSourceSceneBinding.Source provider(String prefix,NativeSceneSnapshot original,int kind){return (epoch,serial,begin,end)->{
  for(int i=0;i<original.geometryCount();i++){NativeScenePacket packet=original.geometry(i);if(original.epoch==epoch&&packet.serial==serial&&packet.beginRefresh==begin&&packet.endRefresh==end){try{return component(prefix,i,kind);}catch(Exception e){throw new IllegalArgumentException("Frozen component read",e);}}}
  throw new IllegalArgumentException("Frozen source identity not found");
 };}
 private JSONObject replay(String prefix)throws Exception{
  byte[] raw=component(prefix,0,0);NativeBackgroundScene original=new NativeBackgroundScene(raw);NativeSceneSnapshot snapshot=original.sky.scene;
  byte[] rebound=NativeSourceBackgroundBinding.bind(raw,new NativeSourceSceneBinding(),provider(prefix,snapshot,1));
  NativeRetainedScene retained=NativeRetainedScene.capture(rebound,provider(prefix,snapshot,2),provider(prefix,snapshot,3),provider(prefix,snapshot,4));ok(retained!=null,"Complete frozen retained capture");
  NativeSceneComposition composition=retained.prepared.composition;int strictFailures=0,commands=0;
  for(int owner=0;owner<composition.count();owner++){NativeSceneDrawPlan plan=composition.plan(owner);commands+=plan.count();for(int i=0;i<plan.count();i++){NativeSceneDrawPlan.Draw d=plan.draw(i);FloatBuffer v=d.mesh();for(int vertex=0;vertex<d.vertices;vertex+=3){try{new NativeTexturePlane(v,vertex);}catch(IllegalArgumentException failure){ok(d.model,"Unexpected world failure");new NativeTexturePlane(v,vertex,true);strictFailures++;}}}}
  ok(strictFailures>0,"Frozen scene did not reproduce strict model rejection");JSONArray images=new JSONArray();
  for(int size=0;size<2;size++){
   int width=size==0?240:3840,height=size==0?160:2160,active=size==0?240:3240;int[] name={0};GLES20.glActiveTexture(GLES20.GL_TEXTURE0);GLES20.glGenTextures(1,name,0);int texture=name[0];GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,texture);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_MIN_FILTER,GLES20.GL_NEAREST);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_MAG_FILTER,GLES20.GL_NEAREST);GLES20.glTexImage2D(GLES20.GL_TEXTURE_2D,0,GLES20.GL_RGBA,width,height,0,GLES20.GL_RGBA,GLES20.GL_UNSIGNED_BYTE,null);GLES20.glGenFramebuffers(1,name,0);int fbo=name[0];GLES20.glBindFramebuffer(GLES20.GL_FRAMEBUFFER,fbo);GLES20.glFramebufferTexture2D(GLES20.GL_FRAMEBUFFER,GLES20.GL_COLOR_ATTACHMENT0,GLES20.GL_TEXTURE_2D,texture,0);ok(GLES20.glCheckFramebufferStatus(GLES20.GL_FRAMEBUFFER)==GLES20.GL_FRAMEBUFFER_COMPLETE,"Frozen framebuffer");
   try(NativeBackgroundSceneGpu gpu=new NativeBackgroundSceneGpu()){
    int triangles=gpu.drawRetained(retained,width,height,active,height);ok(triangles>0,"Frozen geometry did not render");pixels.clear();pixels.limit(width*height*4);GLES20.glReadPixels(0,0,width,height,GLES20.GL_RGBA,GLES20.GL_UNSIGNED_BYTE,pixels);ok(GLES20.glGetError()==GLES20.GL_NO_ERROR,"Frozen complete GPU readback");
    int nonblack=0;for(int i=0;i<width*height;i++)if((pixels.get(i*4)|pixels.get(i*4+1)|pixels.get(i*4+2))!=0)nonblack++;ok(nonblack>0,"Frozen complete image empty");
    JSONObject image=new JSONObject();image.put("width",width);image.put("height",height);image.put("active_width",active);image.put("triangles",triangles);image.put("nonblack_pixels",nonblack);image.put("sha256",digest(pixels));images.put(image);
    if(size==0){try(java.nio.channels.FileChannel channel=new FileOutputStream(new File(getTargetContext().getFilesDir(),prefix+"-240.rgba")).getChannel()){ByteBuffer copy=pixels.duplicate();while(copy.hasRemaining())channel.write(copy);}}
   }finally{GLES20.glBindFramebuffer(GLES20.GL_FRAMEBUFFER,0);GLES20.glDeleteFramebuffers(1,new int[]{fbo},0);GLES20.glDeleteTextures(1,new int[]{texture},0);}
  }
  JSONObject item=new JSONObject();item.put("fixture",prefix);item.put("epoch",snapshot.epoch);item.put("refresh",snapshot.refresh);item.put("owners",snapshot.geometryCount());item.put("commands",commands);item.put("strict_model_plane_failures_recovered",strictFailures);item.put("images",images);return item;
 }
 @Override public void onStart(){Bundle result=new Bundle();boolean live=false;try{
  startGl();live=true;int[] cap={0};GLES20.glGetIntegerv(GLES20.GL_MAX_TEXTURE_SIZE,cap,0);ok(cap[0]>=3840,"4K texture target unavailable");
  String[] names={"point","horizontal","vertical","duplicate_ac","duplicate_ab","duplicate_bc","thin","visible"};
  float[][] shapes={{100,87,100,87,100,87},{50,87,100,87,150,87},{100,40,100,80,100,120},{50,40,150,120,50,40},{50,40,50,40,150,120},{50,40,150,120,150,120},{50,87.25f,150,87.25f,100,87.75f},{50,40,150,40,100,120}};
  JSONArray cases=new JSONArray();String smallEmpty=null,smallThin=null;
  for(int size=0;size<2;size++){String blank=null;for(int i=0;i<shapes.length;i++){JSONObject item=draw(names[i],shapes[i],size==0?240:3840,size==0?160:2160,size==0?240:3240,i<6);String hash=item.getString("sha256");if(i==0)blank=hash;if(i<6)ok(hash.equals(blank),"Empty triangle changed background");if(size==0&&i==0)smallEmpty=hash;if(size==0&&i==6)smallThin=hash;cases.put(item);}}
  endGl();live=false;startGl();live=true;ok(draw("point_recreated",shapes[0],240,160,240,true).getString("sha256").equals(smallEmpty),"Empty context recreation");ok(draw("thin_recreated",shapes[6],240,160,240,false).getString("sha256").equals(smallThin),"Thin context recreation");
  JSONArray scenes=new JSONArray();scenes.put(replay("scene3593"));scenes.put(replay("scene3800"));
  JSONObject report=new JSONObject();report.put("result","PASS_ANDROID_EMPTY_MODEL_ACTUAL_SCENE_SHADER_GLES");report.put("api",Build.VERSION.SDK_INT);report.put("renderer",renderer);report.put("version",version);report.put("cases",cases);report.put("context_recreated",true);report.put("actual_native_scene_program",true);report.put("frozen_complete_retained_scenes",scenes);report.put("full_scene",true);report.put("live_gameplay",false);report.put("real_time_pacing",false);report.put("physical_device",false);
  try(FileOutputStream out=getTargetContext().openFileOutput("empty-model-plane-gpu-report.json",android.content.Context.MODE_PRIVATE)){out.write(report.toString(2).getBytes("UTF-8"));}result.putString("stream",report.toString());finish(Activity.RESULT_OK,result);
 }catch(Throwable failure){android.util.Log.e("NFSUGEmptyModelGPU","Failed",failure);result.putString("stream","FAIL: "+failure);finish(Activity.RESULT_CANCELED,result);}finally{if(live)endGl();}}
}
