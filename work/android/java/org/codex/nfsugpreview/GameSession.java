package org.codex.nfsugpreview;

import android.os.*;

import java.nio.*;

import java.util.concurrent.atomic.AtomicInteger;

final class GameSession {

 interface Status {void message(String message);}

 final AtomicInteger keys=new AtomicInteger();

 volatile byte[] frame;
 final NativePresentation presentation=new NativePresentation();
 final NativeWorkProfile profile=new NativeWorkProfile();
 private boolean retainedCaptureReady;
 private long lastRetainedRefresh=-1;
 volatile long nativePresentationAttempts,nativePresentationAccepted,nativeCompleteScenes,nativeLegacySceneCopiesAvoided,nativeSceneAliases;
 volatile NativeScenePacket nativePacket;
 volatile NativeSceneSnapshot nativeScene;
 volatile long nativeScenesCopied,nativeScenesUnavailable;
 private long lastSceneRefresh=-1;
 volatile long nativePacketsCopied;
 private long captureEpoch=-1,capturePublished,captureRejected,captureFailed;

 volatile boolean requestedActive;

 private final HandlerThread thread=new HandlerThread("NFSUG-Core");

 private final Handler handler;

 private final PrivateStore store;

 private volatile Status status;
 private volatile String lastStatus;

 private final PreviewAudio audio=new PreviewAudio();

 private NativeCore core;

 private boolean wasActive,closed;

 private long previous,lastReport;
 private long runtimeFrames;

 private double accumulated;

 private final double stepSeconds=280896.0/16777216.0;

 private final ByteBuffer pixels=ByteBuffer.allocateDirect(NativeCore.FRAME_BYTES);

 private final short[] samples=new short[8192];

 GameSession(PrivateStore store,Status status){

  this.store=store;this.status=status;thread.start();handler=new Handler(thread.getLooper());handler.post(tick);

 }

 void open(){handler.post(()->{

  try{

   if(core!=null){save();core.close();core=null;}

   presentation.invalidate();retainedCaptureReady=false;lastRetainedRefresh=-1;
   nativePacket=null;nativeScene=null;nativeScenesCopied=nativeScenesUnavailable=0;lastSceneRefresh=-1;nativePacketsCopied=0;captureEpoch=-1;capturePublished=captureRejected=captureFailed=0;
   core=new NativeCore(store.file("game.gba").getAbsolutePath());

   byte[] battery=store.read("battery.sav",131072);

   if(battery!=null&&!core.loadBattery(battery))throw new IllegalStateException("Saved battery file is incompatible");

   byte[] checkpoint=store.read("resume.state",1024*1024);

   if(checkpoint!=null&&!core.loadCheckpoint(checkpoint))throw new IllegalStateException("Resume checkpoint could not be loaded");

   if(PreviewBuild.NATIVE_CAPTURE&&(!core.captureSupported()||!core.capture(true)||!core.captureLayers(true)))throw new IllegalStateException("Native capture could not start");
   configureRetainedCapture();
   android.util.Log.i("NFSUGPreview","CORE_OPEN frequency="+core.timing()[0]+" cycles="+core.timing()[1]);
   core.pause(true);wasActive=false;previous=0;accumulated=0;

   notifyStatus(presentation.enabled()?"Experimental native display; original fallback when needed":"Original display — native toggle available for testing");

  }catch(Exception e){if(core!=null){core.close();core=null;}notifyStatus("Could not start: "+e.getMessage());}

 });}

 void active(boolean value){presentation.active(value);requestedActive=value;if(!value)keys.set(0);handler.post(()->{if(!value)pauseAndSave();});}

 private void save(){

  if(core==null)return;

  try{store.write("battery.sav",core.battery());store.write("resume.state",core.checkpoint());}

  catch(Exception e){notifyStatus("Save failed: "+e.getMessage());}

 }

 private void pauseAndSave(){

  if(core!=null){core.pause(true);if(wasActive){save();android.util.Log.i("NFSUGPreview","PAUSED frames="+runtimeFrames);}}

  presentation.invalidate();lastRetainedRefresh=-1;wasActive=false;previous=0;accumulated=0;audio.enabled(false);

 }

 private final Runnable tick=new Runnable(){public void run(){

  if(closed)return;

  try{

   boolean active=requestedActive&&core!=null;

   if(!active){if(wasActive)pauseAndSave();}

   else{

    long now=System.nanoTime();

    if(!wasActive){core.pause(false);audio.enabled(true);wasActive=true;previous=now;accumulated=0;}

    accumulated+=(now-previous)/1e9;previous=now;

    long presentationToken=presentation.token();
    int count=0;

    while(accumulated>=stepSeconds&&count<8){

     long stepStart=profile.start();
     if(core.step(keys.get())!=1)throw new IllegalStateException("Core frame failed");

     profile.end(NativeWorkProfile.STEP,stepStart);
     accumulated-=stepSeconds;count++;runtimeFrames++;
     if(PreviewBuild.NATIVE_CAPTURE){long legacyStart=profile.start();readNativePacket();
      // Native display already captures the complete source scene below. Preserve
      // publication/epoch checks each logic step without copying a second scene.
      if(retainedCaptureReady)nativeLegacySceneCopiesAvoided++;else readNativeScene();
      profile.end(NativeWorkProfile.LEGACY,legacyStart);}

     long audioStart=profile.start();int n=core.audio(samples);audio.offer(samples,n);profile.end(NativeWorkProfile.AUDIO,audioStart);

    }

    if(count>0&&core.frame(pixels)){

     byte[] owned=new byte[NativeCore.FRAME_BYTES];pixels.position(0);pixels.get(owned);frame=owned;
     if(retainedCaptureReady&&presentation.enabled()){
      long[] timing=core.timing();long refresh=timing[2]-1;
      if(refresh>lastRetainedRefresh){
       try{long captureStart=profile.captureStart();NativeRetainedScene retained;try{retained=core.capturedRetainedScene(profile);}finally{profile.captureEnd(captureStart);}
        if(retained==null){nativeScene=null;nativeScenesUnavailable++;}else{publishNativeScene(retained.background.sky.scene,refresh);nativeSceneAliases++;}
        nativePresentationAttempts++;if(retained!=null)nativeCompleteScenes++;if(presentation.publish(presentationToken,captureEpoch,refresh,owned,retained))nativePresentationAccepted++;lastRetainedRefresh=refresh;
       }catch(RuntimeException failure){nativeDisplay(false);notifyStatus("Native source unavailable; original display: "+failure.getMessage());}
      }
     }

    }

    if(runtimeFrames-lastReport>=300){lastReport=runtimeFrames;android.util.Log.i("NFSUGPreview","RUN frames="+runtimeFrames+" core="+core.timing()[3]+" audioDropped="+audio.droppedChunks+" nativeEnabled="+presentation.enabled()+" nativeReady="+retainedCaptureReady+" attempts="+nativePresentationAttempts+" complete="+nativeCompleteScenes+" accepted="+nativePresentationAccepted+" epoch="+captureEpoch+" generation="+presentation.token());}
    if(audio.error!=null){notifyStatus("Audio stopped: "+audio.error);audio.error=null;}

   }

  }catch(Exception e){requestedActive=false;pauseAndSave();notifyStatus("Preview stopped: "+e.getMessage());}

  handler.postDelayed(this,2);

 }};

 void shutdown(){requestedActive=false;keys.set(0);handler.post(()->{

  closed=true;presentation.invalidate();nativePacket=null;nativeScene=null;pauseAndSave();save();if(core!=null){core.close();core=null;}audio.close();thread.quitSafely();

 });}

 boolean nativeDisplayEnabled(){return presentation.enabled();}
 void nativeDisplay(boolean enabled){
  if(enabled&&!PreviewBuild.NATIVE_CAPTURE){notifyStatus("Native display unavailable in this build");return;}
  presentation.enabled(enabled);handler.post(()->{try{configureRetainedCapture();notifyStatus(enabled?"Native renderer experiment — original fallback when unavailable":"Original display");}catch(Exception e){presentation.enabled(false);retainedCaptureReady=false;try{configureRetainedCapture();}catch(Exception cleanup){android.util.Log.w("NFSUGPreview","Native capture cleanup failed",cleanup);}notifyStatus("Native capture unavailable: "+e.getMessage());}});
 }
 void nativeRenderFailed(Exception failure){nativeDisplay(false);handler.post(()->notifyStatus("Native renderer stopped; original display: "+failure.getMessage()));}
 private void configureRetainedCapture(){
  retainedCaptureReady=false;lastRetainedRefresh=-1;presentation.invalidate();if(core==null)return;
  boolean enabled=presentation.enabled();
  if(enabled){if(!core.captureSourceWorld(true)||!core.captureWallHistory(true)||!core.captureSky(true))throw new IllegalStateException("Complete source capture could not start");retainedCaptureReady=true;}
  else if(PreviewBuild.NATIVE_CAPTURE){core.captureSky(false);core.captureWallHistory(false);core.captureSourceWorld(false);}
 }

 // Only data/worker ownership survives Activity recreation; never retain a View.
 void attach(Status listener){
  status=listener;String message=lastStatus;if(message!=null)listener.message(message);
 }
 void detach(Status listener){if(status==listener)status=null;}
 private void notifyStatus(String message){
  lastStatus=message;Status listener=status;if(listener!=null)listener.message(message);
 }

 private void readNativeScene(){
  byte[] bytes=core.capturedScene();
  if(bytes==null){nativeScene=null;nativeScenesUnavailable++;return;}
  publishNativeScene(new NativeSceneSnapshot(bytes),core.timing()[2]-1);
 }
 private void publishNativeScene(NativeSceneSnapshot owned,long expectedRefresh){
  if(owned.epoch!=captureEpoch||owned.refresh!=expectedRefresh||owned.refresh<=lastSceneRefresh)throw new IllegalStateException("Combined scene source identity changed");
  nativeScene=owned;lastSceneRefresh=owned.refresh;nativeScenesCopied++;
 }
 private void readNativePacket(){
  long[] stats=core.captureStats();if(stats==null||stats.length!=8)throw new IllegalStateException("Native capture status unavailable");
  if(stats[1]!=captureEpoch){nativePacket=null;nativeScene=null;lastSceneRefresh=-1;presentation.invalidate();lastRetainedRefresh=-1;captureEpoch=stats[1];capturePublished=stats[3]-(stats[6]>0?1:0);captureRejected=stats[4];captureFailed=stats[5];}
  if(stats[4]!=captureRejected||stats[5]!=captureFailed){nativePacket=null;captureRejected=stats[4];captureFailed=stats[5];}
  if(stats[3]!=capturePublished){
   if(stats[3]!=capturePublished+1)throw new IllegalStateException("Native capture publication gap");
   byte[] packet=core.capturedPacket();if(packet==null)throw new IllegalStateException("Native packet unavailable");
   NativeScenePacket owned=new NativeScenePacket(captureEpoch,packet);
   if(owned.serial!=stats[7])throw new IllegalStateException("Native scene identity changed");
   nativePacket=owned;nativePacketsCopied++;capturePublished=stats[3];
  }
 }

}

