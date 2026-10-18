package org.codex.nfsugpreview;
import android.app.*;import android.content.*;import android.os.*;
import java.io.*;import java.nio.*;import java.nio.file.*;import java.security.*;import java.util.*;import java.util.zip.CRC32;import java.util.concurrent.atomic.AtomicReference;import org.json.*;
public final class BundleInstrumentation extends Instrumentation {
 int malformed=0,rows=0;void ok(boolean b,String why){if(!b)throw new AssertionError(why);}
 String sha(ByteBuffer b)throws Exception{MessageDigest d=MessageDigest.getInstance("SHA-256");d.update(b);StringBuilder s=new StringBuilder();for(byte v:d.digest())s.append(String.format("%02x",v&255));return s.toString();}
 void reject(byte[] original,int offset,long value){byte[] bad=original.clone();ByteBuffer.wrap(bad).order(ByteOrder.LITTLE_ENDIAN).putLong(offset,value);try{new NativeSceneSnapshot(bad);throw new AssertionError("Accepted malformed "+offset);}catch(IllegalArgumentException good){malformed++;}}
 @Override public void onCreate(Bundle b){super.onCreate(b);start();}
 @Override public void onStart(){Bundle result=new Bundle();try{
  File files=getTargetContext().getFilesDir();byte[] state=Files.readAllBytes(new File(files,"capture-test.state").toPath());List<String> frameHashes=Files.readAllLines(new File(files,"capture-rgba-hashes.txt").toPath());List<String> crcRefs=Files.readAllLines(new File(files,"bundle-crc-reference.tsv").toPath());
  NativeSceneSnapshot[] retained=new NativeSceneSnapshot[2];String[] retainedHashes=new String[2];int whole=0,split=0,missing=0;long pcmFrames=0;MessageDigest sound=MessageDigest.getInstance("SHA-256");ByteBuffer pixels=ByteBuffer.allocateDirect(NativeCore.FRAME_BYTES);short[] pcm=new short[8192];
  NativeCore core=new NativeCore(new File(files,"capture-test.gba").getAbsolutePath());try{
   ok(core.captureSupported()&&core.loadCheckpoint(state)&&core.capture(true)&&core.captureLayers(true),"Combined capture unavailable");long initial=core.timing()[2];
   AtomicReference<Throwable> wrong=new AtomicReference<>();Thread t=new Thread(()->{try{core.capturedScene();wrong.set(new AssertionError("Wrong owner accepted"));}catch(IllegalStateException good){}});t.start();t.join();ok(wrong.get()==null,"Thread owner guard");
   for(int i=0;i<600;i++){
    ok(core.step(1|(i>=60&&i<120?16:i>=480&&i<540?32:0))==1,"Step");long[] timing=core.timing();ok(timing[0]==16777216&&timing[1]==280896&&timing[2]==initial+i+1&&timing[3]==i+1,"Timing");
    pixels.position(0);ok(core.frame(pixels)&&sha(pixels).equals(frameHashes.get(i)),"Original RGBA "+i);int n=core.audio(pcm);pcmFrames+=n;byte[] audio=new byte[n*4];for(int j=0;j<n*2;j++){audio[j*2]=(byte)pcm[j];audio[j*2+1]=(byte)(pcm[j]>>8);}sound.update(audio);
    byte[] raw=core.capturedScene();String[] expected=crcRefs.get(i).split("\t");if(raw==null){ok(i<6&&Long.parseLong(expected[1])==0,"Missing scene");missing++;continue;}
    CRC32 crc=new CRC32();crc.update(raw);ok(raw.length==Long.parseLong(expected[1])&&crc.getValue()==Long.parseLong(expected[2]),"Bundle differs from host "+i);
    NativeSceneSnapshot scene=new NativeSceneSnapshot(raw);ok(scene.refresh==timing[2]-1,"Scene refresh");int index=scene.kind-1;
    if(retained[index]==null){
     List<String> rowHashes=Files.readAllLines(new File(files,index==0?"whole-rows.txt":"split-rows.txt").toPath());ok(rowHashes.size()==160,"Row fixture");for(int y=0;y<160;y++){ok(sha(scene.row(y)).equals(rowHashes.get(y)),"Decoded row "+y);rows++;}
     for(int offset:new int[]{0,8,16,24,32,40,56,64,72,80,120})reject(raw,offset,offset==32?-1:0);
     int layer=(int)ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN).getLong(96);byte[] bad=raw.clone();bad[layer+20512]=(byte)255;bad[layer+20513]=(byte)255;try{new NativeSceneSnapshot(bad);throw new AssertionError("Bad page ref");}catch(IllegalArgumentException good){malformed++;}
     retained[index]=scene;retainedHashes[index]=sha(scene.data());
    }
    Arrays.fill(raw,(byte)165);ok(scene.data().getLong(0)==0x3142414eL,"Input alias");scene.data().position(5);ok(scene.data().position()==0,"Buffer position");try{scene.data().put(0,(byte)0);throw new AssertionError("Mutable scene");}catch(ReadOnlyBufferException good){}
    if(scene.kind==1)whole++;else split++;
   }
   ok(whole==481&&split==113&&missing==6&&rows==320&&malformed==24,"Scene counts");long[] before=core.timing();ok(core.pause(true),"Pause");for(int i=0;i<10;i++)ok(core.step(1)==2&&Arrays.equals(before,core.timing()),"Paused timing");ok(core.pause(false),"Resume");ok(core.loadCheckpoint(state)&&core.capturedScene()==null,"State invalidation");
   for(int i=0;i<16;i++)ok(core.step(1)==1,"Restored step");ok(core.capturedScene()!=null,"Capture did not resume");ok(core.captureLayers(false)&&core.capturedScene()==null,"Layer detach");
  }finally{core.close();}
  for(int i=0;i<2;i++)ok(sha(retained[i].data()).equals(retainedHashes[i]),"Scene lifetime");StringBuilder digest=new StringBuilder();for(byte v:sound.digest())digest.append(String.format("%02x",v&255));ok(pcmFrames==443007&&digest.toString().equals("eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e"),"PCM changed");
  JSONObject report=new JSONObject();report.put("result","PASS_ANDROID_COMBINED_SCENE_JNI");report.put("original_frames",600);report.put("original_timing",true);report.put("pcm_frames",pcmFrames);report.put("scene_crc_matches",594);report.put("whole",whole);report.put("split",split);report.put("initial_missing",missing);report.put("decoded_rows",rows);report.put("malformed_rejected",malformed);report.put("owned_readonly",true);report.put("owner_guard",true);report.put("survives_core_close",true);report.put("state_load_resumes",true);report.put("api",Build.VERSION.SDK_INT);report.put("gpu_rendering",false);report.put("real_time_pacing",false);
  try(FileOutputStream out=getTargetContext().openFileOutput("bundle-jni-report.json",Context.MODE_PRIVATE)){out.write(report.toString(2).getBytes("UTF-8"));}result.putString("stream",report.toString());finish(Activity.RESULT_OK,result);
 }catch(Throwable e){android.util.Log.e("NFSUGBundleJNI","Failed",e);result.putString("stream","FAIL: "+e);finish(Activity.RESULT_CANCELED,result);}}
}
