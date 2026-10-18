package org.codex.nfsugpreview;
import android.app.*;import android.os.*;import android.opengl.*;
import java.io.*;import java.nio.*;import org.json.*;
/** Frozen repaired endpoint through actual retained GPU renderer; no running core. */
public final class RecoveredSceneGpuInstrumentation extends SceneGpuInstrumentation {
 private final ByteBuffer pixels=ByteBuffer.allocateDirect(3840*2160*4);
 private String prefix;
 @Override public void onCreate(Bundle args){prefix=args.getString("fixturePrefix","");if(!prefix.matches("[A-Za-z0-9_-]{1,96}"))throw new AssertionError("Fixture prefix");super.onCreate(args);}
 byte[] component(String prefix,int owner,int kind)throws Exception{return java.nio.file.Files.readAllBytes(new File(getTargetContext().getFilesDir(),prefix+"-owner"+owner+"-kind"+kind+".bin").toPath());}
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
  JSONArray images=new JSONArray();
  for(int size=0;size<2;size++){
   int width=size==0?240:3840,height=size==0?160:2160,active=size==0?240:3240;int[] name={0};GLES20.glActiveTexture(GLES20.GL_TEXTURE0);GLES20.glGenTextures(1,name,0);int texture=name[0];GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,texture);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_MIN_FILTER,GLES20.GL_NEAREST);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_MAG_FILTER,GLES20.GL_NEAREST);GLES20.glTexImage2D(GLES20.GL_TEXTURE_2D,0,GLES20.GL_RGBA,width,height,0,GLES20.GL_RGBA,GLES20.GL_UNSIGNED_BYTE,null);GLES20.glGenFramebuffers(1,name,0);int fbo=name[0];GLES20.glBindFramebuffer(GLES20.GL_FRAMEBUFFER,fbo);GLES20.glFramebufferTexture2D(GLES20.GL_FRAMEBUFFER,GLES20.GL_COLOR_ATTACHMENT0,GLES20.GL_TEXTURE_2D,texture,0);ok(GLES20.glCheckFramebufferStatus(GLES20.GL_FRAMEBUFFER)==GLES20.GL_FRAMEBUFFER_COMPLETE,"Frozen framebuffer");
   try(NativeBackgroundSceneGpu gpu=new NativeBackgroundSceneGpu()){
    int triangles=gpu.drawRetained(retained,width,height,active,height);ok(triangles>0,"Frozen geometry did not render");pixels.clear();pixels.limit(width*height*4);GLES20.glReadPixels(0,0,width,height,GLES20.GL_RGBA,GLES20.GL_UNSIGNED_BYTE,pixels);ok(GLES20.glGetError()==GLES20.GL_NO_ERROR,"Frozen complete GPU readback");
    int nonblack=0;for(int i=0;i<width*height;i++)if((pixels.get(i*4)|pixels.get(i*4+1)|pixels.get(i*4+2))!=0)nonblack++;ok(nonblack>0,"Frozen complete image empty");
    JSONObject image=new JSONObject();image.put("width",width);image.put("height",height);image.put("active_width",active);image.put("triangles",triangles);image.put("nonblack_pixels",nonblack);image.put("sha256",digest(pixels));images.put(image);
    if(true){try(java.nio.channels.FileChannel channel=new FileOutputStream(new File(getTargetContext().getFilesDir(),prefix+"-"+width+".rgba")).getChannel()){ByteBuffer copy=pixels.duplicate();while(copy.hasRemaining())channel.write(copy);}}
   }finally{GLES20.glBindFramebuffer(GLES20.GL_FRAMEBUFFER,0);GLES20.glDeleteFramebuffers(1,new int[]{fbo},0);GLES20.glDeleteTextures(1,new int[]{texture},0);}
  }
  JSONObject item=new JSONObject();item.put("fixture",prefix);item.put("epoch",snapshot.epoch);item.put("refresh",snapshot.refresh);item.put("owners",snapshot.geometryCount());item.put("commands",commands);item.put("strict_model_plane_failures_recovered",strictFailures);item.put("images",images);return item;
 }

 @Override public void onStart(){Bundle result=new Bundle();boolean live=false;try{
  startGl();live=true;int[] limit={0};GLES20.glGetIntegerv(GLES20.GL_MAX_TEXTURE_SIZE,limit,0);ok(limit[0]>=3840,"4K framebuffer unsupported");
  JSONObject first=replay(prefix);ok(first.getLong("epoch")==2&&first.getLong("refresh")==12359&&first.getInt("owners")==2,"Recovered source endpoint identity");
  endGl();live=false;startGl();live=true;JSONObject repeated=replay(prefix);ok(first.getJSONArray("images").toString().equals(repeated.getJSONArray("images").toString()),"Retained image differs after context recreation");
  JSONObject report=new JSONObject();report.put("result","PASS_RECOVERED_SCENE518_RETAINED_GPU");report.put("api",Build.VERSION.SDK_INT);report.put("renderer",renderer);report.put("version",version);report.put("scene",first);report.put("context_recreated",true);report.put("actual_retained_renderer",true);report.put("live_gameplay",false);report.put("real_time_pacing",false);report.put("physical_device",false);report.put("full_scene_60fps",false);
  try(FileOutputStream out=new FileOutputStream(new File(getTargetContext().getFilesDir(),prefix+"-gpu-report.json"))){out.write(report.toString(2).getBytes("UTF-8"));}result.putString("stream",report.toString());finish(Activity.RESULT_OK,result);
 }catch(Throwable failure){android.util.Log.e("NFSUGRecoveredGPU","Failed",failure);result.putString("stream","FAIL: "+failure);finish(Activity.RESULT_CANCELED,result);}finally{if(live)endGl();}}
}
