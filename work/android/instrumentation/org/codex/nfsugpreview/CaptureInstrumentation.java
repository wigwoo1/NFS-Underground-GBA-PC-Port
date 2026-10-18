package org.codex.nfsugpreview;
import android.app.*;import android.content.*;import android.os.*;
import java.io.*;import java.nio.*;import java.nio.file.*;import java.security.*;import java.util.*;import java.util.concurrent.atomic.AtomicReference;
import org.json.*;
public final class CaptureInstrumentation extends Instrumentation {
 private void ok(boolean x,String why){if(!x)throw new AssertionError(why);}
 private String sha(ByteBuffer b)throws Exception{MessageDigest d=MessageDigest.getInstance("SHA-256");d.update(b);return hex(d.digest());}
 private String sha(byte[] b)throws Exception{return hex(MessageDigest.getInstance("SHA-256").digest(b));}
 private String hex(byte[] bytes){StringBuilder s=new StringBuilder();for(byte b:bytes)s.append(String.format("%02x",b&255));return s.toString();}
 @Override public void onCreate(Bundle b){super.onCreate(b);start();}
 @Override public void onStart(){
  Bundle result=new Bundle();
  try{
   File files=getTargetContext().getFilesDir();
   byte[] state=Files.readAllBytes(new File(files,"capture-test.state").toPath());
   List<String> frames=Files.readAllLines(new File(files,"capture-rgba-hashes.txt").toPath());
   List<String> packets=Files.readAllLines(new File(files,"capture-packet-hashes.txt").toPath());
   NativeScenePacket first=null;String firstHash=null;int count=0;long published=0;long pcmFrames=0;
   ByteBuffer pixels=ByteBuffer.allocateDirect(NativeCore.FRAME_BYTES);short[] pcm=new short[8192];MessageDigest sound=MessageDigest.getInstance("SHA-256");
   NativeCore core=new NativeCore(new File(files,"capture-test.gba").getAbsolutePath());
   try{
    ok(core.captureSupported()&&core.loadCheckpoint(state)&&core.capture(true),"Capture not available");
    long initial=core.timing()[2];
    for(int i=0;i<600;i++){
     ok(core.step(1|(i>=60&&i<120?16:i>=480&&i<540?32:0))==1,"Core step");
     ok(core.frame(pixels),"Frame copy");pixels.position(0);
     ok(sha(pixels).equals(frames.get(i)),"RGBA mismatch "+i);
     long[] clock=core.timing();ok(clock[0]==16777216&&clock[1]==280896&&clock[2]==initial+i+1&&clock[3]==i+1,"Original timing");
     int n=core.audio(pcm);pcmFrames+=n;byte[] bytes=new byte[n*4];
     for(int j=0;j<n*2;j++){bytes[j*2]=(byte)pcm[j];bytes[j*2+1]=(byte)(pcm[j]>>8);}sound.update(bytes);
     long[] stats=core.captureStats();ok(stats!=null&&stats.length==8&&stats[4]==0&&stats[5]==0,"Capture status");
     if(stats[3]!=published){
      ok(stats[3]==published+1,"Lost packet");byte[] raw=core.capturedPacket();ok(raw!=null,"No packet");
      String digest=sha(raw);ok(digest.equals(packets.get(count)),"Packet differs from PC "+count);
      NativeScenePacket scene=new NativeScenePacket(stats[1],raw);
      ok(scene.serial==stats[7]&&scene.endRefresh<=clock[2],"Packet identity");
      for(int section=0;section<5;section++){
       ByteBuffer header=ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN);int offset=header.getInt(36+section*12),size=header.getInt(40+section*12);
       ByteBuffer expected=ByteBuffer.wrap(raw,offset,size).slice();
       ok(scene.section(section).remaining()==size&&sha(scene.section(section)).equals(sha(expected)),"Section copy");
      }
      boolean readOnly=false;try{scene.data().put(0,(byte)0);}catch(ReadOnlyBufferException expected){readOnly=true;}ok(readOnly,"Mutable packet");
      scene.data().position(7);ok(scene.data().position()==0,"Shared buffer position");
      Arrays.fill(raw,(byte)0);ok(sha(scene.data()).equals(digest)&&sha(core.capturedPacket()).equals(digest),"Packet alias");
      if(first==null){first=scene;firstHash=digest;}count++;published=stats[3];
     }
    }
    ok(count==148&&count==packets.size(),"Capture count");
    AtomicReference<Throwable> problem=new AtomicReference<>();
    Thread wrong=new Thread(()->{try{core.capturedPacket();problem.set(new AssertionError("Wrong owner accepted"));}catch(IllegalStateException expected){}});
    wrong.start();wrong.join();ok(problem.get()==null,"Thread guard");
    long[] paused=core.timing();ok(core.pause(true),"Pause");
    for(int i=0;i<10;i++)ok(core.step(1)==2&&Arrays.equals(core.timing(),paused),"Paused step");
    ok(core.pause(false),"Resume");long epoch=core.captureStats()[1];
    ok(core.loadCheckpoint(state)&&core.captureStats()[1]>epoch&&core.capturedPacket()==null,"Epoch invalidation");
    for(int i=0;i<16;i++)ok(core.step(1)==1,"Restored step");
    ok(sha(core.capturedPacket()).equals(packets.get(2)),"Capture after load");
    ok(core.capture(false)&&core.capturedPacket()==null,"Detach");
   }finally{core.close();}
   ok(first!=null&&sha(first.data()).equals(firstHash),"Owned packet invalid after close");
   ok(pcmFrames==443007&&hex(sound.digest()).equals("eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e"),"PCM changed");
   byte[] malformed=new byte[92];boolean bad=false;try{new NativeScenePacket(1,malformed);}catch(IllegalArgumentException expected){bad=true;}ok(bad,"Malformed Java packet accepted");
   JSONObject report=new JSONObject();report.put("result","PASS_ANDROID_JNI_CAPTURE");report.put("original_rgba_frames",600);report.put("original_timing",true);
   report.put("pc_identical_packets",count);report.put("sections_verified",count*5);report.put("audio_pcm_frames",pcmFrames);report.put("owner_guard",true);
   report.put("copied_readonly_packet",true);report.put("owned_packet_survives_core_close",true);report.put("state_load_capture_resumes",true);
   report.put("api",Build.VERSION.SDK_INT);report.put("gpu_scene_rendering",false);report.put("real_time_pacing",false);
   try(FileOutputStream out=getTargetContext().openFileOutput("capture-jni-report.json",Context.MODE_PRIVATE)){out.write(report.toString(2).getBytes("UTF-8"));}
   result.putString("stream",report.toString());finish(Activity.RESULT_OK,result);
  }catch(Throwable e){android.util.Log.e("NFSUGCaptureJNI","Test failed",e);result.putString("stream","FAIL: "+e);finish(Activity.RESULT_CANCELED,result);}
 }
}
