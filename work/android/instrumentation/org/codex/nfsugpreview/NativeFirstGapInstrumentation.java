package org.codex.nfsugpreview;
import android.app.*;import android.os.*;import java.io.*;import java.nio.*;import java.nio.file.*;import java.lang.reflect.*;import java.security.*;import java.util.*;import org.json.*;
/** Bounded read-only component witness after the first confirmed route gap. */
public class NativeFirstGapInstrumentation extends Instrumentation {
 private boolean expectGap=true,traceProgress;private int steps=100,witnessStep=82;private String prefix;private byte[][] baseline;private byte[] baselineAudio,state;private long baselineSamples;private int[] keys;private JSONObject witness;
 private void require(boolean b,String why){if(!b)throw new AssertionError(why);}
 protected File file(String suffix){return new File(getTargetContext().getFilesDir(),prefix+suffix);}
 private String hex(byte[] b){StringBuilder s=new StringBuilder();for(byte v:b)s.append(String.format("%02x",v&255));return s.toString();}
 private JSONArray array(long[] values){JSONArray a=new JSONArray();for(long v:values)a.put(v);return a;}
 private JSONObject describe(String suffix,byte[] bytes)throws Exception{JSONObject r=new JSONObject();r.put("present",bytes!=null);if(bytes!=null){r.put("bytes",bytes.length);r.put("sha256",hex(MessageDigest.getInstance("SHA-256").digest(bytes)));try(FileOutputStream out=new FileOutputStream(file(suffix))){out.write(bytes);}}return r;}
 @Override public void onCreate(Bundle args){super.onCreate(args);expectGap=!"false".equals(args.getString("expectGap","true"));traceProgress="true".equals(args.getString("progress","false"));steps=Integer.parseInt(args.getString("steps","100"));witnessStep=Integer.parseInt(args.getString("witnessStep","82"));require(steps>=1&&steps<=6000&&witnessStep>=1&&witnessStep<=steps,"Bounded witness range");baseline=new byte[steps][];keys=new int[steps];prefix=args.getString("fixturePrefix","");require(prefix.matches("[A-Za-z0-9_-]{1,96}"),"Fixture prefix");start();}
 protected JSONObject captureContext(NativeCore core)throws Exception{return null;}
 protected JSONArray classifyOwner(NativeCore core,NativeScenePacket packet){return null;}
 private JSONObject inspect(NativeCore core)throws Exception{
  JSONObject r=new JSONObject();long[] before=core.timing();r.put("timing",array(before));r.put("capture_stats",array(core.captureStats()));
  Method method=NativeCore.class.getDeclaredMethod("captureBackgroundSceneNative",long.class);method.setAccessible(true);byte[] raw=(byte[])method.invoke(null,core.ownerHandle());r.put("original_background",describe("-background.bin",raw));
  r.put("legacy_combined_scene",describe("-legacy-scene.bin",core.capturedScene()));JSONArray owners=new JSONArray();
  if(raw!=null){NativeBackgroundScene background=new NativeBackgroundScene(raw);NativeSceneSnapshot scene=background.sky.scene;r.put("epoch",scene.epoch);r.put("refresh",scene.refresh);r.put("kind",scene.kind);r.put("split_row",scene.splitRow);
   for(int i=0;i<scene.geometryCount();i++){
    NativeScenePacket packet=scene.geometry(i);JSONObject owner=new JSONObject();owner.put("owner",i);owner.put("serial",packet.serial);owner.put("begin",packet.beginRefresh);owner.put("end",packet.endRefresh);owner.put("page",packet.page);
    owner.put("world",describe("-owner"+i+"-world.bin",core.capturedSourceWorld(scene.epoch,packet.serial,packet.beginRefresh,packet.endRefresh)));
    owner.put("classifier",classifyOwner(core,packet));
    owner.put("road",describe("-owner"+i+"-road.bin",core.capturedRoadHistory(scene.epoch,packet.serial,packet.beginRefresh,packet.endRefresh)));
    owner.put("wall",describe("-owner"+i+"-wall.bin",core.capturedWallHistory(scene.epoch,packet.serial,packet.beginRefresh,packet.endRefresh)));
    owner.put("proof",describe("-owner"+i+"-proof.bin",core.capturedWriteOwnership(scene.epoch,packet.serial,packet.beginRefresh,packet.endRefresh)));owners.put(owner);
   }
  }
  r.put("owners",owners);r.put("source_background_retry",describe("-source-background-retry.bin",core.capturedSourceBackgroundScene()));r.put("retained_retry_present",core.capturedRetainedScene()!=null);r.put("capture_context",captureContext(core));require(Arrays.equals(before,core.timing()),"Component reads advanced game timing");r.put("reads_preserved_clock",true);return r;
 }
 private JSONObject phase(boolean capture)throws Exception{
  ByteBuffer pixels=ByteBuffer.allocateDirect(NativeCore.FRAME_BYTES);short[] sound=new short[8192];byte[] serialized=new byte[16384];MessageDigest frame=MessageDigest.getInstance("SHA-256"),pcm=MessageDigest.getInstance("SHA-256");long samples=0;JSONArray missing=new JSONArray();
  try(NativeCore core=new NativeCore(file(".gba").getAbsolutePath())){
   require(core.loadCheckpoint(state),"Checkpoint");if(capture)require(core.capture(true)&&core.captureLayers(true)&&core.captureSourceWorld(true)&&core.captureWallHistory(true)&&core.captureSky(true),"Capture enable");long first=core.timing()[2];require(core.pause(false),"Unpause");
   for(int step=1;step<=steps;step++){
    require(core.step(keys[step-1])==1,"Step");long[] t=core.timing();require(t[0]==16777216&&t[1]==280896&&t[2]==first+step&&t[3]==step,"Clock");require(core.frame(pixels),"Original display");pixels.position(0);frame.reset();frame.update(pixels);byte[] hash=frame.digest();if(capture)require(Arrays.equals(hash,baseline[step-1]),"Original image changed");else baseline[step-1]=hash;
    int n=core.audio(sound);require(n>=0&&n<=4096,"PCM count");for(int i=0;i<n*2;i++){serialized[i*2]=(byte)sound[i];serialized[i*2+1]=(byte)(sound[i]>>8);}pcm.update(serialized,0,n*4);samples+=n;
    if(capture){NativeRetainedScene retained=core.capturedRetainedScene();if(retained==null)missing.put(step);
     if(step==witnessStep){require((retained==null)==expectGap,"Unexpected capture outcome at witness step "+witnessStep);witness=inspect(core);require(core.frame(pixels),"Post-read original frame");pixels.position(0);frame.reset();frame.update(pixels);require(Arrays.equals(frame.digest(),hash),"Readout changed original pixels");require(core.audio(sound)==0,"Readout changed PCM queue");witness.put("reads_preserved_original_pixels_pcm",true);}
    }
    if(traceProgress&&step%300==0){JSONObject progress=new JSONObject();progress.put("phase",capture?"native":"original");progress.put("step",step);progress.put("missing",missing.length());Files.write(file("-progress.json").toPath(),progress.toString().getBytes("UTF-8"));}
   }
  }
  byte[] hash=pcm.digest();if(capture)require(samples==baselineSamples&&Arrays.equals(hash,baselineAudio),"PCM changed");else{baselineSamples=samples;baselineAudio=hash;}
  JSONObject r=new JSONObject();r.put("steps",steps);r.put("audio_frames",samples);r.put("audio_sha256",hex(hash));r.put("missing_steps",missing);return r;
 }
 @Override public void onStart(){Bundle result=new Bundle();try{
  state=Files.readAllBytes(file(".state").toPath());JSONArray ledger=new JSONArray(new String(Files.readAllBytes(file("-keys.json").toPath()),"UTF-8"));require(ledger.length()>=steps,"Ledger");for(int i=0;i<steps;i++){keys[i]=ledger.getInt(i);require(keys[i]>=0&&keys[i]<=1023,"Input key mask");}
  JSONObject original=phase(false),nativeResult=phase(true);JSONObject report=new JSONObject();report.put("result","VERIFIED_ANDROID_FIRST_GAP_COMPONENT_WITNESS");report.put("original",original);report.put("native",nativeResult);report.put("witness_step",witnessStep);report.put("step"+witnessStep,witness);report.put("paired_original_pixels_pcm_clocks_exact",true);report.put("gpu",false);report.put("unpaced",true);report.put("full_scene_60fps",false);
  try(FileOutputStream out=new FileOutputStream(file("-report.json"))){out.write(report.toString(2).getBytes("UTF-8"));}result.putString("stream",report.toString());finish(Activity.RESULT_OK,result);
 }catch(Throwable e){android.util.Log.e("NFSUGFirstGap","Failed",e);result.putString("stream","FAIL: "+e);finish(Activity.RESULT_CANCELED,result);}}
}
