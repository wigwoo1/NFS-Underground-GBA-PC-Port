package org.codex.nfsugpreview;
import android.app.*;
import android.accessibilityservice.AccessibilityService;
import android.content.*;
import android.os.*;
import android.view.*;import android.widget.*;import android.graphics.Bitmap;import android.opengl.GLES20;import java.nio.file.*;import java.util.concurrent.*;
import java.io.*;
import java.lang.reflect.*;
import java.util.*;
import org.json.*;
/** Device instrumentation of actual injected MotionEvents; not physical-touch proof. */
public final class PreviewNativeUiInstrumentation extends Instrumentation {
 private PreviewActivity activity;
 private TouchOverlay overlay;
 private GameSession session;
 private float width,height,ox,oy,u;
 private long downTime;
 private int checks;
 private final List<String> passed=new ArrayList<>();
 private void require(boolean value,String message){if(!value)throw new AssertionError(message);}
 private Object field(Object owner,String name)throws Exception{
  Class<?> type=owner.getClass();while(type!=null){try{Field f=type.getDeclaredField(name);f.setAccessible(true);return f.get(owner);}catch(NoSuchFieldException absent){type=type.getSuperclass();}}throw new NoSuchFieldException(name);
 }
 private String fixturePrefix="background-test";
 @Override public void onCreate(Bundle args){super.onCreate(args);if(args!=null)fixturePrefix=args.getString("fixturePrefix","background-test");require(fixturePrefix.matches("[A-Za-z0-9_-]{1,96}"),"Invalid fixture prefix");FixturePreviewActivity.TEST_ROOT="preview-ui-test-"+UUID.randomUUID();start();}
 private void geometry(){
  runOnMainSync(()->{int[] pos=new int[2];overlay.getLocationOnScreen(pos);ox=pos[0];oy=pos[1];width=overlay.getWidth();height=overlay.getHeight();u=Math.min(width*.075f,height*.15f);});
  require(width>0&&height>0,"Overlay not laid out");
 }
 private float[] a(){return new float[]{width*.88f,height*.62f};}
 private float[] b(){return new float[]{width*.76f,height*.78f};}
 private float[] startButton(){return new float[]{width*.57f,height*.88f};}
 private float[] select(){return new float[]{width*.43f,height*.88f};}
 private float[] direction(float dx,float dy){return new float[]{width*.14f+u*dx,height*.66f+u*dy};}
 private void event(int action,int[] ids,float[][] points,int expected){
  if((action&255)==MotionEvent.ACTION_DOWN)downTime=SystemClock.uptimeMillis();
  MotionEvent.PointerProperties[] props=new MotionEvent.PointerProperties[ids.length];
  MotionEvent.PointerCoords[] coords=new MotionEvent.PointerCoords[ids.length];
  for(int i=0;i<ids.length;i++){
   props[i]=new MotionEvent.PointerProperties();props[i].id=ids[i];props[i].toolType=MotionEvent.TOOL_TYPE_FINGER;
   coords[i]=new MotionEvent.PointerCoords();coords[i].x=ox+points[i][0];coords[i].y=oy+points[i][1];coords[i].pressure=1;coords[i].size=.1f;
  }
  MotionEvent e=MotionEvent.obtain(downTime,SystemClock.uptimeMillis(),action,ids.length,props,coords,0,0,1,1,0,0,InputDevice.SOURCE_TOUCHSCREEN,0);
  try{sendPointerSync(e);}finally{e.recycle();}
  waitForIdleSync();
  require(session.keys.get()==expected,"Event "+checks+" expected "+expected+" got "+session.keys.get());checks++;
 }
 private void button(float[] p,int bits){
  event(MotionEvent.ACTION_DOWN,new int[]{2},new float[][]{p},bits);
  event(MotionEvent.ACTION_UP,new int[]{2},new float[][]{p},0);
 }
 private void awaitActive(boolean active)throws Exception{
  for(int i=0;i<100;i++){
   final boolean[] value={false};runOnMainSync(()->value[0]=overlay.isEnabled());
   if(value[0]==active&&session.requestedActive==active)return;
   Thread.sleep(20);
  }
  throw new AssertionError("Activity active/enabled did not become "+active);
 }
 private void controls()throws Exception{
  awaitActive(true);geometry();
  button(a(),1);button(b(),2);button(select(),4);button(startButton(),8);
  button(direction(1,0),16);button(direction(-1,0),32);button(direction(0,-1),64);button(direction(0,1),128);
  button(direction(1,-1),80);button(direction(-1,1),160);
  passed.add("all eight requested buttons and diagonals");

  event(0,new int[]{2},new float[][]{a()},1);
  event(5|(1<<8),new int[]{2,5},new float[][]{a(),direction(1,-1)},81);
  event(5|(2<<8),new int[]{2,5,9},new float[][]{a(),direction(1,-1),a()},81);
  event(6,new int[]{2,5,9},new float[][]{a(),direction(1,-1),a()},81);
  event(2,new int[]{5,9},new float[][]{direction(-1,1),a()},161);
  event(6,new int[]{5,9},new float[][]{direction(-1,1),a()},1);
  event(1,new int[]{9},new float[][]{a()},0);
  passed.add("A plus diagonal, duplicate-held A, independent pointer release and drag");

  event(0,new int[]{2},new float[][]{direction(1,0)},16);
  event(5|(1<<8),new int[]{2,5},new float[][]{direction(1,0),direction(-1,0)},0);
  event(5|(2<<8),new int[]{2,5,9},new float[][]{direction(1,0),direction(-1,0),b()},2);
  event(6|(1<<8),new int[]{2,5,9},new float[][]{direction(1,0),direction(-1,0),b()},18);
  event(3,new int[]{2,9},new float[][]{direction(1,0),b()},0);
  passed.add("opposite direction neutralization and ACTION_CANCEL");

  event(0,new int[]{2},new float[][]{a()},1);
  event(2,new int[]{2},new float[][]{new float[]{width*.5f,height*.25f}},0);
  event(1,new int[]{2},new float[][]{new float[]{width*.5f,height*.25f}},0);
  passed.add("pointer dragged outside buttons");

  event(0,new int[]{2},new float[][]{a()},1);
  require(getUiAutomation().performGlobalAction(AccessibilityService.GLOBAL_ACTION_HOME),"Could not send Home");
  awaitActive(false);require(session.keys.get()==0,"Focus loss left input held");
  passed.add("real Home focus loss clears held A and disables controls");
  // Resume externally, as a launcher/user does. Background app starts can be denied.
  getUiAutomation().waitForIdle(200,3000);
  try(InputStream launch=new ParcelFileDescriptor.AutoCloseInputStream(
    getUiAutomation().executeShellCommand("am start -W -n org.codex.nfsugpreview/.FixturePreviewActivity"))){
   byte[] bytes=new byte[1024];while(launch.read(bytes)!=-1){}
  }
  awaitActive(true);geometry();require(session.keys.get()==0,"Resume restored held input");
  button(a(),1);passed.add("resume accepts new input without stuck A");
 }

 interface Condition{boolean ready()throws Exception;}
 private void until(Condition condition,String why)throws Exception{long end=System.nanoTime()+45000000000L;while(!condition.ready()){if(System.nanoTime()>end)throw new AssertionError(why+" status="+field(activity,"status")+" enabled="+(session!=null&&session.nativeDisplayEnabled()));Thread.sleep(20);}}
 private void launch()throws Exception{activity=(PreviewActivity)startActivitySync(new Intent(getTargetContext(),FixturePreviewActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK));waitForIdleSync();overlay=(TouchOverlay)field(activity,"controls");session=(GameSession)field(activity,"session");awaitActive(true);until(()->session.frame!=null,"No original frame");}
 private void closePreview()throws Exception{if(activity==null)return;Thread worker=(Thread)field(session,"thread");runOnMainSync(()->activity.finish());worker.join(10000);require(!worker.isAlive(),"Core owner not released on exit");activity=null;}
 private long[] timing()throws Exception{Handler h=(Handler)field(session,"handler");CountDownLatch done=new CountDownLatch(1);final long[][] value={null};h.post(()->{try{NativeCore core=(NativeCore)read(session,"core");if(core!=null)value[0]=core.timing();}finally{done.countDown();}});require(done.await(5,TimeUnit.SECONDS),"Core not responding");return value[0];}
 private Object read(Object owner,String name){try{return field(owner,name);}catch(Exception e){throw new RuntimeException(e);}}
 private Button findButton(View v,String needle){if(v instanceof Button&&((Button)v).getText().toString().toLowerCase().contains(needle))return (Button)v;if(v instanceof ViewGroup){ViewGroup g=(ViewGroup)v;for(int n=0;n<g.getChildCount();n++){Button b=findButton(g.getChildAt(n),needle);if(b!=null)return b;}}return null;}
 private void click(String needle){runOnMainSync(()->{Button button=findButton(activity.getWindow().getDecorView(),needle);require(button!=null,"Missing button "+needle);button.performClick();});}
 private FrameView view()throws Exception{return (FrameView)field(activity,"view");}
 @Override public void onStart(){Bundle result=new Bundle();try{
  File files=getTargetContext().getFilesDir(),root=new File(files,FixturePreviewActivity.TEST_ROOT);require(root.mkdir(),"Unique fixture directory already exists");Files.copy(new File(files,fixturePrefix+".gba").toPath(),new File(root,"game.gba").toPath());
  launch();require(!session.nativeDisplayEnabled(),"Native mode should default off");long[] bootBefore=timing();click("native");Thread.sleep(1200);long[] bootAfter=timing();require(bootBefore!=null&&bootAfter!=null&&bootAfter[3]>bootBefore[3],"Boot native fallback stopped original game");require(view().originalFramesRendered>0,"Boot original fallback absent");closePreview();passed.add("ROM boots through ordinary UI with native fallback");
  for(String name:new String[]{"resume.state","resume.state.bak","resume.state.new","battery.sav","battery.sav.bak","battery.sav.new"})Files.deleteIfExists(new File(root,name).toPath());Files.copy(new File(files,fixturePrefix+".state").toPath(),new File(root,"resume.state").toPath());
  launch();GameSession retained=session;click("native");until(()->view().nativeFramesRendered>=3,"No ordinary UI native display");NativePresentation.Frame before=session.presentation.latest();require(before!=null&&before.scene!=null,"Missing complete scene");long refresh=before.refresh;until(()->{NativePresentation.Frame f=session.presentation.latest();return f!=null&&f.scene!=null&&f.refresh>refresh;},"Scene did not move");
  CountDownLatch gl=new CountDownLatch(1);final boolean[] clean={false};view().probe=(f,x,y,w,h)->{if(f!=null){clean[0]=GLES20.glGetError()==GLES20.GL_NO_ERROR;try{view().probe=null;}catch(Exception ignored){}gl.countDown();}};require(gl.await(15,TimeUnit.SECONDS)&&clean[0],"Ordinary UI native GL error");
  Bitmap image=getUiAutomation().takeScreenshot();require(image!=null,"Screenshot unavailable");try(FileOutputStream output=getTargetContext().openFileOutput("preview-native-ui.png",0)){require(image.compress(Bitmap.CompressFormat.PNG,100,output),"Screenshot export");}finally{image.recycle();}passed.add("ordinary toolbar native toggle and moving source display");
  click("pause");awaitActive(false);require(session.presentation.latest()==null,"Pause retained native frame");long[] paused=timing();NativeSceneSnapshot pausedScene=session.nativeScene;long aliases=session.nativeSceneAliases;require(pausedScene!=null&&aliases>0&&session.nativeLegacySceneCopiesAvoided>0,"Native scene alias unavailable");PreviewActivity old=activity;runOnMainSync(()->old.recreate());until(()->FixturePreviewActivity.current!=old,"No replacement UI");activity=FixturePreviewActivity.current;waitForIdleSync();overlay=(TouchOverlay)field(activity,"controls");session=(GameSession)field(activity,"session");require(session.nativeScene==pausedScene&&session.nativeSceneAliases==aliases,"Recreation changed paused source alias");require(session==retained&&(Boolean)field(activity,"userPaused"),"UI recreation lost native session or pause");long[] after=timing();require(after[2]==paused[2]&&after[3]==paused[3]&&session.keys.get()==0,"Paused recreation advanced game");require(session.nativeDisplayEnabled()&&session.presentation.latest()==null,"Recreation restored stale native image");click("resume");awaitActive(true);until(()->view().nativeFramesRendered>=3,"Native UI recreation did not resume");passed.add("paused Activity recreation preserves core and clears native presentation");
  click("native");require(!session.nativeDisplayEnabled(),"Native off button");long fallback=view().originalFramesRendered;until(()->view().originalFramesRendered>fallback+2,"Native off did not show original");click("native");long nativeCount=view().nativeFramesRendered;until(()->view().nativeFramesRendered>nativeCount+2,"Native on did not resume");passed.add("ordinary buttons switch original/native presentation");
  controls();long nativePresentations=view().nativeFramesRendered;closePreview();
  JSONObject report=new JSONObject();report.put("result","PASS_ANDROID_PREVIEW_NATIVE_UI");report.put("event_assertions",checks);report.put("passed",new JSONArray(passed));report.put("native_presentations",nativePresentations);report.put("ordinary_preview_activity_inherited",true);report.put("isolated_test_saves",true);report.put("boot_fallback",true);report.put("race_checkpoint_native_display",true);report.put("paused_activity_recreation",true);report.put("normal_exit_releases_core",true);report.put("physical_touch",false);report.put("complete_race",false);report.put("full_scene_60fps",false);try(FileOutputStream out=getTargetContext().openFileOutput("preview-native-ui-report.json",0)){out.write(report.toString(2).getBytes("UTF-8"));}result.putString("stream",report.toString());finish(Activity.RESULT_OK,result);
 }catch(Throwable failure){android.util.Log.e("NFSUGPreviewUI","Failed",failure);result.putString("stream","FAIL after "+checks+" event assertions: "+failure);finish(Activity.RESULT_CANCELED,result);}finally{try{closePreview();}catch(Exception ignored){}}}
}
