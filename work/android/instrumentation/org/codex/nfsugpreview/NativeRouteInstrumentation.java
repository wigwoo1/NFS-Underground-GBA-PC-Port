package org.codex.nfsugpreview;
import android.app.*;import android.os.*;import java.io.*;import java.nio.*;import java.nio.file.*;import java.security.*;import java.util.*;import org.json.*;
/** Paired original-clock/source capture coverage. Deliberately unpaced, no GPU/audio device. */
public final class NativeRouteInstrumentation extends Instrumentation {
 private String prefix;private final int steps=6000;private byte[][] baselineFrames=new byte[steps][];private byte[] baselineAudio;private long baselineSamples;private byte[] state;private int[] keys=new int[steps];private String phase="setup";private int step;
 private void require(boolean b,String text){if(!b)throw new AssertionError(text);}
 @Override public void onCreate(Bundle args){super.onCreate(args);prefix=args.getString("fixturePrefix","");require(prefix.matches("[A-Za-z0-9_-]{1,96}"),"Fixture prefix");start();}
 private File file(String suffix){return new File(getTargetContext().getFilesDir(),prefix+suffix);}
 private String hex(byte[] bytes){StringBuilder text=new StringBuilder();for(byte b:bytes)text.append(String.format("%02x",b&255));return text.toString();}
 private void progress(String value)throws Exception{try(FileOutputStream out=new FileOutputStream(file("-progress.json"))){out.write(value.getBytes("UTF-8"));}}
 private JSONObject run(boolean capture)throws Exception{
  phase=capture?"native":"original";JSONArray missing=new JSONArray(),failed=new JSONArray(),details=new JSONArray();int captured=0,planes=0,strictModelFailures=0;long samples=0;double maxStep=0,maxCapture=0;long start=System.nanoTime();MessageDigest pcm=MessageDigest.getInstance("SHA-256"),frames=MessageDigest.getInstance("SHA-256"),single=MessageDigest.getInstance("SHA-256");ByteBuffer pixels=ByteBuffer.allocateDirect(NativeCore.FRAME_BYTES);short[] sound=new short[8192];byte[] serialized=new byte[16384];
  try(NativeCore core=new NativeCore(file(".gba").getAbsolutePath())){
   require(core.loadCheckpoint(state),"Checkpoint load");
   if(capture)require(core.captureSupported()&&core.capture(true)&&core.captureLayers(true)&&core.captureSourceWorld(true)&&core.captureWallHistory(true)&&core.captureSky(true),"Native capture enable");
   long first=core.timing()[2];require(core.pause(false),"Unpause");
   for(step=1;step<=steps;step++){
    long began=System.nanoTime();require(core.step(keys[step-1])==1,"Step");maxStep=Math.max(maxStep,(System.nanoTime()-began)/1e6);long[] timing=core.timing();require(timing.length==4&&timing[0]==16777216&&timing[1]==280896&&timing[2]==first+step&&timing[3]==step,"Original clock differs at "+step);
    require(core.frame(pixels),"Original pixels");pixels.position(0);pixels.limit(NativeCore.FRAME_BYTES);single.reset();single.update(pixels);byte[] hash=single.digest();frames.update(hash);if(capture)require(Arrays.equals(hash,baselineFrames[step-1]),"Original frame changed at "+step);else baselineFrames[step-1]=hash;
    int n=core.audio(sound);require(n>=0&&n<=4096,"PCM bounds");for(int i=0;i<n*2;i++){serialized[i*2]=(byte)sound[i];serialized[i*2+1]=(byte)(sound[i]>>8);}pcm.update(serialized,0,n*4);samples+=n;
    if(capture){long beganCapture=System.nanoTime();try{
     NativeRetainedScene retained=core.capturedRetainedScene();if(retained==null)missing.put(step);else{
      require(retained.refresh==timing[2]-1,"Source refresh mismatch");NativeSceneComposition composition=retained.prepared.composition;
      for(int owner=0;owner<composition.count();owner++){NativeSceneDrawPlan plan=composition.plan(owner);for(int command=0;command<plan.count();command++){NativeSceneDrawPlan.Draw draw=plan.draw(command);FloatBuffer vertices=draw.mesh();for(int vertex=0;vertex<draw.vertices;vertex+=3){new NativeTexturePlane(vertices,vertex,draw.model);planes++;if(draw.model){try{new NativeTexturePlane(vertices,vertex);}catch(IllegalArgumentException empty){strictModelFailures++;}}}}}
      captured++;
     }
    }catch(RuntimeException failure){failed.put(step);if(details.length()<32){JSONObject e=new JSONObject();e.put("step",step);e.put("reason",failure.toString());details.put(e);}}finally{maxCapture=Math.max(maxCapture,(System.nanoTime()-beganCapture)/1e6);}}
    if(step%300==0){JSONObject status=new JSONObject();status.put("phase",phase);status.put("step",step);status.put("captured",captured);status.put("missing",missing.length());status.put("failed",failed.length());progress(status.toString());android.util.Log.i("NFSUGNativeRoute",status.toString());}
   }
  }
  byte[] audioHash=pcm.digest();if(capture){require(samples==baselineSamples&&Arrays.equals(audioHash,baselineAudio),"Original PCM changed");}else{baselineSamples=samples;baselineAudio=audioHash;}
  require(samples==4430117&&hex(audioHash).equals("e3d0620b037591b5e4d2fb1e806448e2635eb056d614dd3710942a3c6b645807"),"PC route PCM oracle differs");
  JSONObject r=new JSONObject();r.put("phase",phase);r.put("steps",steps);r.put("original_frame_hash_chain",hex(frames.digest()));r.put("original_audio_frames",samples);r.put("original_audio_sha256",hex(audioHash));r.put("captured_preflighted_scenes",captured);r.put("missing_steps",missing);r.put("preparation_failure_steps",failed);r.put("failure_details",details);r.put("triangle_planes_checked",planes);r.put("strict_model_plane_failures_recovered",strictModelFailures);r.put("diagnostic_elapsed_seconds",(System.nanoTime()-start)/1e9);r.put("max_core_step_ms",maxStep);r.put("max_source_capture_preflight_ms",maxCapture);return r;
 }
 @Override public void onStart(){Bundle result=new Bundle();try{
  state=Files.readAllBytes(file(".state").toPath());JSONArray ledger=new JSONArray(new String(Files.readAllBytes(file("-keys.json").toPath()),"UTF-8"));require(ledger.length()==steps,"Route ledger size");for(int i=0;i<steps;i++){keys[i]=ledger.getInt(i);require(keys[i]>=0&&keys[i]<=1023,"Route key mask");}
  JSONObject original=run(false),nativeResult=run(true);require(original.getString("original_frame_hash_chain").equals(nativeResult.getString("original_frame_hash_chain")),"Frame chain changed");
  JSONObject report=new JSONObject();report.put("result","VERIFIED_ANDROID_PAIRED_ROUTE_ORIGINAL_PARITY_CAPTURE_COVERAGE_RECORDED");report.put("original",original);report.put("native",nativeResult);report.put("all_original_pixels_audio_clocks_exact",true);report.put("api",Build.VERSION.SDK_INT);report.put("gpu_each_scene_verified",false);report.put("diagnostic_unpaced",true);report.put("audio_device_used",false);report.put("full_race",false);report.put("full_scene_60fps",false);report.put("physical_device",false);
  try(FileOutputStream out=new FileOutputStream(file("-report.json"))){out.write(report.toString(2).getBytes("UTF-8"));}result.putString("stream",report.toString());finish(Activity.RESULT_OK,result);
 }catch(Throwable failure){android.util.Log.e("NFSUGNativeRoute","Failed "+phase+" "+step,failure);result.putString("stream","FAIL phase="+phase+" step="+step+" "+failure);finish(Activity.RESULT_CANCELED,result);}}
}
