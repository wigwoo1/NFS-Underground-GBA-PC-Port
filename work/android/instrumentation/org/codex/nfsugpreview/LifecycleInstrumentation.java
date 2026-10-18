package org.codex.nfsugpreview;
import android.app.*;
import android.content.*;
import android.os.*;
import android.view.*;
import android.widget.*;
import java.io.*;
import java.lang.reflect.*;
import java.util.concurrent.*;
import org.json.*;
public final class LifecycleInstrumentation extends Instrumentation {
 private PreviewActivity activity;
 private Object field(Object object,String name)throws Exception{
  Field f=object.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(object);
 }
 private void require(boolean x,String why){if(!x)throw new AssertionError(why);}
 private Button pauseButton(View v){
  if(v instanceof Button){String s=((Button)v).getText().toString().toLowerCase();if(s.contains("pause")||s.equals("resume"))return (Button)v;}
  if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int i=0;i<g.getChildCount();i++){Button b=pauseButton(g.getChildAt(i));if(b!=null)return b;}}
  return null;
 }
 private long[] timing(GameSession session)throws Exception{
  Handler h=(Handler)field(session,"handler");CountDownLatch done=new CountDownLatch(1);
  final long[][] out={null};final Throwable[] error={null};
  h.post(()->{try{NativeCore core=(NativeCore)field(session,"core");if(core!=null)out[0]=core.timing();}catch(Throwable e){error[0]=e;}finally{done.countDown();}});
  require(done.await(3,TimeUnit.SECONDS),"Core owner thread did not respond");
  if(error[0]!=null)throw new AssertionError(error[0]);return out[0];
 }
 private long[] ready(GameSession session)throws Exception{
  for(int i=0;i<100;i++){long[] t=timing(session);if(t!=null&&session.frame!=null)return t;Thread.sleep(20);}
  throw new AssertionError("Core/frame did not become ready");
 }
 private int threads(String name){
  int n=0;for(Thread thread:Thread.getAllStackTraces().keySet())if(thread.isAlive()&&thread.getName().equals(name))n++;return n;
 }
 @Override public void onCreate(Bundle b){super.onCreate(b);start();}
 @Override public void onStart(){
  Bundle result=new Bundle();
  try{
   activity=(PreviewActivity)startActivitySync(new Intent(getTargetContext(),PreviewActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));
   waitForIdleSync();GameSession original=(GameSession)field(activity,"session");ready(original);
   if(PreviewBuild.NATIVE_CAPTURE){for(int i=0;i<150&&original.nativeScene==null;i++)Thread.sleep(20);require(original.nativePacket!=null&&original.nativeScene!=null,"App worker did not publish combined native scene");}
   runOnMainSync(()->{Button b=pauseButton(activity.getWindow().getDecorView());require(b!=null,"Pause button missing");b.performClick();});
   waitForIdleSync();long[] before=timing(original);require(before!=null&&!original.requestedActive,"Pause did not reach owner");
   byte[] frame=original.frame;
   NativeScenePacket nativePacket=original.nativePacket;long copied=original.nativePacketsCopied;
   NativeSceneSnapshot nativeScene=original.nativeScene;long scenesCopied=original.nativeScenesCopied;
   for(int iteration=0;iteration<3;iteration++){
    ActivityMonitor monitor=new ActivityMonitor(PreviewActivity.class.getName(),null,false);addMonitor(monitor);
    runOnMainSync(()->activity.recreate());
    Activity replacement=monitor.waitForActivityWithTimeout(5000);removeMonitor(monitor);
    require(replacement instanceof PreviewActivity&&replacement!=activity,"Replacement Activity not observed");
    activity=(PreviewActivity)replacement;waitForIdleSync();
    GameSession current=(GameSession)field(activity,"session");
    require(current==original,"Recreation replaced the core-owning session");
    require((Boolean)field(activity,"userPaused"),"Recreation lost user pause");
    long[] after=timing(current);require(after!=null&&after[2]==before[2]&&after[3]==before[3],"Paused recreation advanced/reset core");
    require(current.frame==frame,"Recreation discarded owned paused frame");
    require(current.nativePacket==nativePacket&&current.nativePacketsCopied==copied,"Recreation changed paused native packet");
    require(current.nativeScene==nativeScene&&current.nativeScenesCopied==scenesCopied,"Recreation changed paused combined scene");
    require(current.keys.get()==0&&!current.requestedActive,"Recreation restored held input");
    require(threads("NFSUG-Core")==1&&threads("NFSUG-Audio")==1,"Recreation leaked owner/audio threads");
   }
   runOnMainSync(()->pauseButton(activity.getWindow().getDecorView()).performClick());
   long[] later=null;
   for(int i=0;i<100;i++){later=timing(original);if(later[2]>before[2])break;Thread.sleep(20);}
   require(later!=null&&later[2]>before[2],"Retained core did not resume");
   runOnMainSync(()->pauseButton(activity.getWindow().getDecorView()).performClick());
   runOnMainSync(()->activity.finish());
   for(int i=0;i<150&&(threads("NFSUG-Core")!=0||threads("NFSUG-Audio")!=0);i++)Thread.sleep(20);
   require(threads("NFSUG-Core")==0&&threads("NFSUG-Audio")==0,"Normal exit leaked worker threads");
   try(NativeCore reopened=new NativeCore(new File(getTargetContext().getFilesDir(),"game.gba").getAbsolutePath())){
    require(reopened.timing()[0]==16777216,"Normal exit did not release native singleton");
   }
   JSONObject report=new JSONObject();report.put("result","PASS_ANDROID_ACTIVITY_RECREATION");report.put("recreations",3);
   report.put("same_owner_session",true);report.put("paused_counter_preserved",true);report.put("owned_frame_preserved",true);
   report.put("held_input_cleared",true);report.put("owner_audio_threads_each",1);report.put("resume_advances",true);report.put("normal_exit_threads",0);report.put("fresh_core_after_exit",true);
   report.put("combined_scene_preserved",true);report.put("combined_scenes_copied",scenesCopied);report.put("native_capture",PreviewBuild.NATIVE_CAPTURE);report.put("native_packets_copied",copied);report.put("api",Build.VERSION.SDK_INT);report.put("physical_device",false);report.put("process_death_test",false);
   try(FileOutputStream out=getTargetContext().openFileOutput("lifecycle-instrumentation-report.json",Context.MODE_PRIVATE)){out.write(report.toString(2).getBytes("UTF-8"));}
   result.putString("stream",report.toString());finish(Activity.RESULT_OK,result);
  }catch(Throwable e){android.util.Log.e("NFSUGLifecycleTest","Failed",e);result.putString("stream","FAIL: "+e);finish(Activity.RESULT_CANCELED,result);}
 }
}
