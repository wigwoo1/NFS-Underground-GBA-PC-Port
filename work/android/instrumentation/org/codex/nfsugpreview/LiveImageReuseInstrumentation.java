package org.codex.nfsugpreview;
import android.app.*;import android.os.*;import android.opengl.*;
import java.io.*;import java.nio.*;import org.json.*;
/** Exact pixels and real renderer-call counts; not a motion or FPS test. */
public final class LiveImageReuseInstrumentation extends SceneGpuInstrumentation {
 private String prefix;
 @Override public void onCreate(Bundle args){prefix=args.getString("fixturePrefix","");if(!prefix.matches("[A-Za-z0-9_-]{1,96}"))throw new AssertionError("Fixture prefix");super.onCreate(args);}
 private byte[] component(int owner,int kind)throws Exception{return java.nio.file.Files.readAllBytes(new File(getTargetContext().getFilesDir(),prefix+"-owner"+owner+"-kind"+kind+".bin").toPath());}
 private NativeSourceSceneBinding.Source provider(NativeSceneSnapshot original,int kind){return (epoch,serial,begin,end)->{
  for(int i=0;i<original.geometryCount();i++){NativeScenePacket p=original.geometry(i);if(original.epoch==epoch&&p.serial==serial&&p.beginRefresh==begin&&p.endRefresh==end){try{return component(i,kind);}catch(Exception e){throw new IllegalArgumentException(e);}}}throw new IllegalArgumentException("Fixture identity");
 };}
 private NativeRetainedScene capture()throws Exception{
  byte[] raw=component(0,0);NativeSceneSnapshot snapshot=new NativeBackgroundScene(raw).sky.scene;
  byte[] rebound=NativeSourceBackgroundBinding.bind(raw,new NativeSourceSceneBinding(),provider(snapshot,1));
  NativeRetainedScene result=NativeRetainedScene.capture(rebound,provider(snapshot,2),provider(snapshot,3),provider(snapshot,4));ok(result!=null,"Frozen capture missing");return result;
 }
 private String readTexture(int texture,int w,int h)throws Exception{
  int[] name={0};GLES20.glGenFramebuffers(1,name,0);int fbo=name[0];
  try{GLES20.glBindFramebuffer(GLES20.GL_FRAMEBUFFER,fbo);GLES20.glFramebufferTexture2D(GLES20.GL_FRAMEBUFFER,GLES20.GL_COLOR_ATTACHMENT0,GLES20.GL_TEXTURE_2D,texture,0);ok(GLES20.glCheckFramebufferStatus(GLES20.GL_FRAMEBUFFER)==GLES20.GL_FRAMEBUFFER_COMPLETE,"Read target");ByteBuffer pixels=ByteBuffer.allocateDirect(w*h*4);GLES20.glReadPixels(0,0,w,h,GLES20.GL_RGBA,GLES20.GL_UNSIGNED_BYTE,pixels);ok(GLES20.glGetError()==GLES20.GL_NO_ERROR,"Readback error");return digest(pixels);
  }finally{GLES20.glBindFramebuffer(GLES20.GL_FRAMEBUFFER,0);GLES20.glDeleteFramebuffers(1,new int[]{fbo},0);}
 }
 private String reference(NativeRetainedScene scene,int w,int h)throws Exception{
  int[] name={0};GLES20.glGenTextures(1,name,0);int texture=name[0];GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,texture);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_MIN_FILTER,GLES20.GL_NEAREST);GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D,GLES20.GL_TEXTURE_MAG_FILTER,GLES20.GL_NEAREST);GLES20.glTexImage2D(GLES20.GL_TEXTURE_2D,0,GLES20.GL_RGBA,w,h,0,GLES20.GL_RGBA,GLES20.GL_UNSIGNED_BYTE,null);GLES20.glGenFramebuffers(1,name,0);int fbo=name[0];
  try(NativeBackgroundSceneGpu gpu=new NativeBackgroundSceneGpu()){GLES20.glBindFramebuffer(GLES20.GL_FRAMEBUFFER,fbo);GLES20.glFramebufferTexture2D(GLES20.GL_FRAMEBUFFER,GLES20.GL_COLOR_ATTACHMENT0,GLES20.GL_TEXTURE_2D,texture,0);ok(GLES20.glCheckFramebufferStatus(GLES20.GL_FRAMEBUFFER)==GLES20.GL_FRAMEBUFFER_COMPLETE,"Reference target");ok(gpu.drawRetained(scene,w,h,w,h)>0,"Reference geometry");return readTexture(texture,w,h);
  }finally{GLES20.glBindFramebuffer(GLES20.GL_FRAMEBUFFER,0);GLES20.glDeleteFramebuffers(1,new int[]{fbo},0);GLES20.glDeleteTextures(1,new int[]{texture},0);}
 }
 private void calls(NativeWorkProfile profile,long expected){ok(profile.stage(NativeWorkProfile.PREPARE)[0]==expected,"Unexpected actual composition count; expected "+expected);int[] current={-1};GLES20.glGetIntegerv(GLES20.GL_FRAMEBUFFER_BINDING,current,0);ok(current[0]==0,"Default framebuffer not restored");}
 private JSONObject exercise()throws Exception{
  NativeRetainedScene a=capture(),b=capture();ok(a!=b&&a.epoch==b.epoch&&a.refresh==b.refresh,"Independent equal endpoint control");NativeWorkProfile profile=new NativeWorkProfile();profile.enabled=true;
  String smallReference=reference(a,240,160),largeReference=reference(a,3840,2160);
  try(NativeLiveGpu gpu=new NativeLiveGpu(profile)){
   int texture=gpu.draw(a,240,160);calls(profile,1);ok(readTexture(texture,240,160).equals(smallReference),"Initial reference mismatch");
   for(int i=0;i<100;i++)ok(gpu.draw(a,240,160)==texture,"Repeated scene texture changed");calls(profile,1);ok(readTexture(texture,240,160).equals(smallReference),"Repeated scene pixels changed");
   ok(readTexture(gpu.draw(b,240,160),240,160).equals(smallReference),"Distinct scene pixels");calls(profile,2);
   gpu.draw(a,240,160);calls(profile,3); // Only the latest exact object may be reused.
   boolean rejected=false;try{gpu.draw(null,240,160);}catch(IllegalArgumentException expected){rejected=true;}ok(rejected,"Null scene accepted");rejected=false;try{gpu.draw(a,0,160);}catch(IllegalArgumentException expected){rejected=true;}ok(rejected,"Empty size accepted");gpu.draw(a,240,160);calls(profile,3);
   int large=gpu.draw(a,3840,2160);calls(profile,4);ok(readTexture(large,3840,2160).equals(largeReference),"Resize reference mismatch");for(int i=0;i<100;i++)ok(gpu.draw(a,3840,2160)==large,"4K repeated texture changed");calls(profile,4);ok(readTexture(large,3840,2160).equals(largeReference),"4K repeated pixels changed");
   ok(readTexture(gpu.draw(a,240,160),240,160).equals(smallReference),"Resize-back reference mismatch");calls(profile,5);
  }
  try(NativeLiveGpu reopened=new NativeLiveGpu(profile)){ok(readTexture(reopened.draw(a,240,160),240,160).equals(smallReference),"Closed target reused");calls(profile,6);}
  ok(GLES20.glGetError()==GLES20.GL_NO_ERROR,"Final GL error");JSONObject row=new JSONObject();row.put("original_sha256",smallReference);row.put("four_k_sha256",largeReference);row.put("repeat_draws_skipped",200);row.put("actual_compositions",6);row.put("distinct_object_same_identity_redrawn",true);row.put("resize_and_close_invalidate",true);row.put("invalid_inputs_rejected",true);return row;
 }
 @Override public void onStart(){Bundle result=new Bundle();boolean live=false;try{
  startGl();live=true;JSONObject first=exercise();endGl();live=false;startGl();live=true;JSONObject second=exercise();ok(first.toString().equals(second.toString()),"Context recreation changed reuse/reference results");
  JSONObject report=new JSONObject();report.put("result","PASS_ANDROID_EXACT_SCENE_IMAGE_REUSE");report.put("renderer",renderer);report.put("checks",first);report.put("context_recreated",true);report.put("reference_pixels_exact",true);report.put("full_scene_60fps",false);report.put("live_gameplay",false);report.put("physical_device",false);try(FileOutputStream out=new FileOutputStream(new File(getTargetContext().getFilesDir(),prefix+"-gpu-report.json"))){out.write(report.toString(2).getBytes("UTF-8"));}result.putString("stream",report.toString());finish(Activity.RESULT_OK,result);
 }catch(Throwable failure){android.util.Log.e("NFSUGImageReuse","Failed",failure);result.putString("stream","FAIL: "+failure);finish(Activity.RESULT_CANCELED,result);}finally{if(live)endGl();}}
}
