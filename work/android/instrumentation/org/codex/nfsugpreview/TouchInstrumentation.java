package org.codex.nfsugpreview;
import android.app.*;
import android.accessibilityservice.AccessibilityService;
import android.content.*;
import android.os.*;
import android.view.*;
import java.io.*;
import java.lang.reflect.*;
import java.util.*;
import org.json.*;
/** Device instrumentation of actual injected MotionEvents; not physical-touch proof. */
public final class TouchInstrumentation extends Instrumentation {
 private PreviewActivity activity;
 private TouchOverlay overlay;
 private GameSession session;
 private float width,height,ox,oy,u;
 private long downTime;
 private int checks;
 private final List<String> passed=new ArrayList<>();
 private void require(boolean value,String message){if(!value)throw new AssertionError(message);}
 private Object field(Object owner,String name)throws Exception{
  Field f=owner.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(owner);
 }
 @Override public void onCreate(Bundle args){super.onCreate(args);start();}
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
 // Direct callback recovery test: a fresh gesture must discard orphaned IDs.
 // Unlike event(), this deliberately bypasses framework-generated cancellation.
 private void restartGestureRecovery(){
  runOnMainSync(()->{
   overlay.clear();
   int[] ids={2,9,9};float[][] points={a(),b(),b()};
   for(int i=0;i<3;i++){
    MotionEvent.PointerProperties property=new MotionEvent.PointerProperties();property.id=ids[i];property.toolType=MotionEvent.TOOL_TYPE_FINGER;
    MotionEvent.PointerCoords coords=new MotionEvent.PointerCoords();coords.x=points[i][0];coords.y=points[i][1];coords.pressure=1;coords.size=.1f;
    long time=SystemClock.uptimeMillis();
    MotionEvent event=MotionEvent.obtain(time,time,i==2?MotionEvent.ACTION_UP:MotionEvent.ACTION_DOWN,1,new MotionEvent.PointerProperties[]{property},new MotionEvent.PointerCoords[]{coords},0,0,1,1,0,0,InputDevice.SOURCE_TOUCHSCREEN,0);
    try{overlay.onTouchEvent(event);}finally{event.recycle();}
    require(session.keys.get()==(i==0?1:i==1?2:0),"Fresh gesture retained orphaned input: "+session.keys.get());checks++;
   }

  });
  passed.add("direct callback recovery from an interrupted gesture with a different pointer ID");
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
    getUiAutomation().executeShellCommand("am start -W -n org.codex.nfsugpreview/.PreviewActivity"))){
   byte[] bytes=new byte[1024];while(launch.read(bytes)!=-1){}
  }
  awaitActive(true);geometry();require(session.keys.get()==0,"Resume restored held input");
  button(a(),1);passed.add("resume accepts new input without stuck A");
 }
 @Override public void onStart(){
  Bundle result=new Bundle();
  try{
   Intent intent=new Intent(getTargetContext(),PreviewActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
   activity=(PreviewActivity)startActivitySync(intent);waitForIdleSync();
   overlay=(TouchOverlay)field(activity,"controls");session=(GameSession)field(activity,"session");
   controls();restartGestureRecovery();
   JSONObject report=new JSONObject();report.put("result","PASS_ANDROID_INJECTED_TOUCH");report.put("event_assertions",checks);
   report.put("passed",new JSONArray(passed));report.put("api",Build.VERSION.SDK_INT);report.put("physical_touch",false);
   report.put("native_scene_renderer",false);report.put("complete_race",false);
   try(FileOutputStream out=getTargetContext().openFileOutput("touch-instrumentation-report.json",Context.MODE_PRIVATE)){
    out.write(report.toString(2).getBytes("UTF-8"));
   }
   result.putString("stream",report.toString());finish(Activity.RESULT_OK,result);
  }catch(Throwable e){
   result.putString("stream","FAIL after "+checks+" event assertions; "+passed+": "+e.toString());android.util.Log.e("NFSUGTouchTest","Test failed",e);finish(Activity.RESULT_CANCELED,result);
  }
 }
}
