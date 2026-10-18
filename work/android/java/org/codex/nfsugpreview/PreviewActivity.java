package org.codex.nfsugpreview;

import android.app.*;

import android.content.*;

import android.media.*;

import android.net.Uri;

import android.os.*;

import android.view.*;

import android.widget.*;

import java.io.*;

public class PreviewActivity extends Activity {
 private boolean retainingSession;
 private GameSession.Status statusListener;
 private static final class Retained {
  final GameSession session;final boolean userPaused;
  Retained(GameSession session,boolean userPaused){this.session=session;this.userPaused=userPaused;}
 }


 private GameSession session;private FrameView view;private TouchOverlay controls;private PrivateStore store;

 private Button renderer;
 private TextView status;private AudioManager audio;private AudioFocusRequest focus;

 private boolean resumed,focused,userPaused,hasAudioFocus;

 private void message(String value){runOnUiThread(()->{status.setText(value);if(renderer!=null&&session!=null)renderer.setText(session.nativeDisplayEnabled()?"Native: On":"Native: Off");});}

 @Override public void onCreate(Bundle saved){

  super.onCreate(saved);
  userPaused=saved!=null&&saved.getBoolean("userPaused",false);
  Retained retained=(Retained)getLastNonConfigurationInstance();
  if(retained!=null)userPaused=retained.userPaused;getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

  store=new PrivateStore(getFilesDir());

  FrameLayout root=new FrameLayout(this);setContentView(root);

  status=new TextView(this);status.setTextColor(0xFFFFFFFF);status.setTextSize(12);

  status.setText("Select your supplied ROM — experimental native display available");

  statusListener=this::message;
  session=retained==null?new GameSession(store,statusListener):retained.session;
  if(retained!=null)session.attach(statusListener);view=new FrameView(this,session);root.addView(view);

  controls=new TouchOverlay(this,session);root.addView(controls);

  LinearLayout bar=new LinearLayout(this);bar.setOrientation(LinearLayout.HORIZONTAL);bar.setBackgroundColor(0xAA101010);

  Button open=new Button(this);open.setText("Open ROM");open.setOnClickListener(v->{

   userPaused=true;updateActive();

   Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE);

   startActivityForResult(intent,1);

  });bar.addView(open);

  Button pause=new Button(this);pause.setText(userPaused?"Resume":"Pause / Resume");pause.setOnClickListener(v->{userPaused=!userPaused;pause.setText(userPaused?"Resume":"Pause");updateActive();});bar.addView(pause);

  renderer=new Button(this);renderer.setText(session.nativeDisplayEnabled()?"Native: On":"Native: Off");renderer.setOnClickListener(v->{session.nativeDisplay(!session.nativeDisplayEnabled());renderer.setText(session.nativeDisplayEnabled()?"Native: On":"Native: Off");});bar.addView(renderer);

  bar.addView(status,new LinearLayout.LayoutParams(0,-2,1));

  root.addView(bar,new FrameLayout.LayoutParams(-1,-2,Gravity.TOP));
  bar.addOnLayoutChangeListener((v,l,t,r,b,ol,ot,orr,ob)->{
   int toolbarHeight=b-t;
   if(toolbarHeight>0&&toolbarHeight!=ob-ot){
    for(View content:new View[]{view,controls}){
     FrameLayout.LayoutParams params=(FrameLayout.LayoutParams)content.getLayoutParams();
     params.topMargin=toolbarHeight;content.setLayoutParams(params);
    }
   }
  });

  root.setOnApplyWindowInsetsListener((v,insets)->{

   if(Build.VERSION.SDK_INT>=30){

    android.graphics.Insets safe=insets.getInsets(WindowInsets.Type.systemBars()|WindowInsets.Type.displayCutout());

    root.setPadding(safe.left,safe.top,safe.right,safe.bottom);

   }else root.setPadding(insets.getSystemWindowInsetLeft(),insets.getSystemWindowInsetTop(),insets.getSystemWindowInsetRight(),insets.getSystemWindowInsetBottom());

   return insets;

  });

  audio=(AudioManager)getSystemService(AUDIO_SERVICE);

  focus=new AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN)

   .setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_GAME).build())

   .setOnAudioFocusChangeListener(change->{

    hasAudioFocus=change==AudioManager.AUDIOFOCUS_GAIN;updateActive();

   }).build();

  if(retained==null&&store.file("game.gba").exists())session.open();

 }

 private void updateActive(){

  if(session==null)return;boolean active=resumed&&focused&&!userPaused&&hasAudioFocus;

  if(controls!=null){controls.setEnabled(active);if(!active)controls.clear();}session.active(active);

 }

 @Override protected void onResume(){

  super.onResume();resumed=true;view.onResume();

  hasAudioFocus=audio.requestAudioFocus(focus)==AudioManager.AUDIOFOCUS_REQUEST_GRANTED;updateActive();

 }

 @Override protected void onPause(){

  resumed=false;updateActive();audio.abandonAudioFocusRequest(focus);hasAudioFocus=false;

  view.onPause();super.onPause();

 }

 @Override public void onWindowFocusChanged(boolean value){super.onWindowFocusChanged(value);focused=value;updateActive();}

 @Override protected void onSaveInstanceState(Bundle out){
  out.putBoolean("userPaused",userPaused);super.onSaveInstanceState(out);
 }
 @Override public Object onRetainNonConfigurationInstance(){
  retainingSession=true;session.detach(statusListener);return new Retained(session,userPaused);
 }
 @Override protected void onDestroy(){
  if(session!=null){session.detach(statusListener);if(!retainingSession)session.shutdown();}
  super.onDestroy();
 }

 @Override protected void onActivityResult(int request,int result,Intent data){

  super.onActivityResult(request,result,data);

  if(request!=1||result!=RESULT_OK||data==null){message("ROM selection cancelled — tap Resume to continue");return;}

  Uri uri=data.getData();if(uri==null)return;message("Checking selected ROM…");

  new Thread(()->{

   try(InputStream in=getContentResolver().openInputStream(uri)){

    if(in==null)throw new IOException("Selected file could not be read");

    store.importRom(in);

    runOnUiThread(()->{if(!isDestroyed()&&!isFinishing()){session.open();userPaused=false;updateActive();}});

   }catch(Exception e){message("ROM not imported: "+e.getMessage());}

  },"NFSUG-ROM-import").start();

 }

}

