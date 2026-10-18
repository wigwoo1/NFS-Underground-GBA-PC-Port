package org.codex.nfsugpreview;

import java.nio.ByteBuffer;

/** One live core, exclusively owned by the constructing thread. No Android UI. */

public final class NativeCore implements AutoCloseable {

 static {System.loadLibrary("nfsug_android_core");}

 public static final int WIDTH=240,HEIGHT=160,FRAME_BYTES=WIDTH*HEIGHT*4;

 private final Thread owner=Thread.currentThread();

 private long handle;
 private boolean sourceWorldEnabled;
 private final NativeSourceSceneBinding sourceSceneBinding=new NativeSourceSceneBinding();

 public NativeCore(String romPath){

  if(romPath==null)throw new IllegalArgumentException("ROM path is required");

  handle=openNative(romPath);

  if(handle==0)throw new IllegalStateException("Could not open the supplied NFS Underground ROM, or another core is active");

 }

 long ownerHandle(){check();return handle;}

 private void check(){

  if(Thread.currentThread()!=owner)throw new IllegalStateException("Core call from a different owner thread");

  if(handle==0)throw new IllegalStateException("Core is closed");

 }

 public int step(int keys){check();return stepNative(handle,keys);}

 public boolean pause(boolean paused){check();return pauseNative(handle,paused);}

 public long[] timing(){check();return timingNative(handle);}

 /** Writes tightly packed RGBA, opaque alpha, from offset zero, without changing position. */

 public boolean frame(ByteBuffer output){

  check();

  if(output==null||!output.isDirect()||output.isReadOnly()||output.capacity()<FRAME_BYTES)return false;

  return frameNative(handle,output);

 }

 public int audio(short[] output){check();return audioNative(handle,output);}

 public byte[] checkpoint(){check();return snapshotNative(handle,false);}

 public byte[] battery(){check();return snapshotNative(handle,true);}

 public boolean loadCheckpoint(byte[] bytes){check();boolean ok=restoreNative(handle,bytes,false);if(ok)sourceSceneBinding.clear();return ok;}

 public boolean loadBattery(byte[] bytes){check();return restoreNative(handle,bytes,true);}

 public boolean captureSupported(){check();return captureSupportedNative();}
 public boolean capture(boolean enabled){check();boolean ok=captureEnableNative(handle,enabled);if(ok&&!enabled){sourceWorldEnabled=false;sourceSceneBinding.clear();}return ok;}
 public long[] captureStats(){check();return captureStatsNative(handle);}
 /** New caller-owned array; only the core owner may request a packet. */
 public byte[] capturedPacket(){check();return capturePacketNative(handle);}
 /** Enable exact source-world collection on this core's owner thread. */
 public boolean captureSourceWorld(boolean enabled){check();boolean ok=captureSourceWorldEnableNative(handle,enabled);if(ok){sourceWorldEnabled=enabled;sourceSceneBinding.clear();}return ok;}
 /** Caller-owned source geometry; sky, retained background and HUD are separate. */
 public byte[] capturedSourceWorld(long epoch,long serial,long begin,long end){check();return captureSourceWorldNative(handle,epoch,serial,begin,end);}
 /** Original wall-source component only; complete scene assets remain separate. */
 public boolean captureWallHistory(boolean enabled){check();return captureWallHistoryEnableNative(handle,enabled);}
 public byte[] capturedWallHistory(long epoch,long serial,long begin,long end){check();return captureWallHistoryNative(handle,epoch,serial,begin,end);}
 /** Frozen original road runs and source-write proof for the same scene owner.
     Requires captureWallHistory; neither component alone is a complete frame. */
 public byte[] capturedRoadHistory(long epoch,long serial,long begin,long end){check();return captureRoadHistoryNative(handle,epoch,serial,begin,end);}
 public byte[] capturedWriteOwnership(long epoch,long serial,long begin,long end){check();return captureWriteOwnershipNative(handle,epoch,serial,begin,end);}
 /** Original sky capture, shared with source replay when retention is enabled. */
 public boolean captureSky(boolean enabled){check();return captureSkyEnableNative(handle,enabled);}
 /** Source geometry joined to original sky/background/display layers. Road/wall
     ownership still requires separate retained components before GPU publication. */
 public byte[] capturedSourceBackgroundScene(){NativeSourceBackgroundBinding.Bound result=capturedSourceBackgroundPrepared(null);return result==null?null:result.bytes;}
 private NativeSourceBackgroundBinding.Bound capturedSourceBackgroundPrepared(NativeWorkProfile profile){
  check();if(!sourceWorldEnabled)return null;
  long start=NativeWorkProfile.start(profile);byte[] raw=captureBackgroundSceneNative(handle);NativeWorkProfile.end(profile,NativeWorkProfile.CAPTURE_BG_COPY,start);
  start=NativeWorkProfile.start(profile);
  NativeSourceSceneBinding.Source world=(epoch,serial,begin,end)->{long copyStart=NativeWorkProfile.start(profile);byte[] bytes=capturedSourceWorld(epoch,serial,begin,end);NativeWorkProfile.end(profile,NativeWorkProfile.CAPTURE_WORLD_COPY,copyStart);return bytes;};
  NativeSourceBackgroundBinding.Bound result=NativeSourceBackgroundBinding.bindPrepared(raw,sourceSceneBinding,world);NativeWorkProfile.end(profile,NativeWorkProfile.CAPTURE_BG_BIND,start);return result;
 }
 /** Complete retained endpoint capture. Renderer must still respect epoch changes;
     this does not advance logic or interpolate/present a frame. */
 NativeRetainedScene capturedRetainedScene(){return capturedRetainedScene(null);}
 NativeRetainedScene capturedRetainedScene(NativeWorkProfile profile){check();return NativeRetainedScene.capturePrepared(capturedSourceBackgroundPrepared(profile),this::capturedRoadHistory,this::capturedWallHistory,this::capturedWriteOwnership,profile);}
 public long[] wallHistoryStats(){check();return captureWallHistoryStatsNative(handle);}
 public boolean captureLayers(boolean enabled){check();return captureLayersNative(handle,enabled);}
 /** Owned NAB1 combined scene at the latest complete historical refresh, or null. */
 public byte[] capturedScene(){check();return captureSceneNative(handle);}
 /** NAB1 display snapshot with rebuilt source geometry and original historical
     rows/provenance. Original sky/background/road assets remain separate. */
 public byte[] capturedSourceScene(){
  check();if(!sourceWorldEnabled)return null;byte[] raw=captureSceneNative(handle);if(raw==null)return null;
  NativeSceneSnapshot scene=sourceSceneBinding.bind(new NativeSceneSnapshot(raw),this::capturedSourceWorld);if(scene==null)return null;
  ByteBuffer data=scene.data();byte[] owned=new byte[data.remaining()];data.get(owned);return owned;
 }

 @Override public void close(){

  if(Thread.currentThread()!=owner)throw new IllegalStateException("Close from a different owner thread");

  if(handle!=0){closeNative(handle);handle=0;sourceWorldEnabled=false;sourceSceneBinding.clear();}

 }

 private static native long openNative(String path);

 private static native void closeNative(long handle);

 private static native int stepNative(long handle,int keys);

 private static native boolean pauseNative(long handle,boolean paused);

 private static native long[] timingNative(long handle);

 private static native boolean frameNative(long handle,ByteBuffer output);

 private static native int audioNative(long handle,short[] output);

 private static native byte[] snapshotNative(long handle,boolean battery);

 private static native boolean restoreNative(long handle,byte[] bytes,boolean battery);

 private static native boolean captureSupportedNative();
 private static native boolean captureEnableNative(long handle,boolean enabled);
 private static native long[] captureStatsNative(long handle);
 private static native byte[] capturePacketNative(long handle);
 private static native boolean captureSourceWorldEnableNative(long handle,boolean enabled);
 private static native byte[] captureSourceWorldNative(long handle,long epoch,long serial,long begin,long end);
 private static native boolean captureLayersNative(long handle,boolean enabled);
 private static native byte[] captureSceneNative(long handle);

 private static native boolean captureWallHistoryEnableNative(long handle,boolean enabled);
 private static native byte[] captureWallHistoryNative(long handle,long epoch,long serial,long begin,long end);
 private static native long[] captureWallHistoryStatsNative(long handle);

 private static native byte[] captureRoadHistoryNative(long handle,long epoch,long serial,long begin,long end);
 private static native byte[] captureWriteOwnershipNative(long handle,long epoch,long serial,long begin,long end);

 private static native boolean captureSkyEnableNative(long handle,boolean enabled);
 private static native byte[] captureBackgroundSceneNative(long handle);

}

