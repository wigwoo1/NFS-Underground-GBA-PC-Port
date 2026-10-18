package org.codex.nfsugpreview;
import android.app.*;import android.content.*;import android.os.*;
import java.io.*;import java.nio.*;import java.nio.file.*;import java.security.*;import java.util.*;import java.util.concurrent.atomic.AtomicReference;
import org.json.*;
public final class SourceWorldInstrumentation extends Instrumentation {
 private void ok(boolean v,String why){if(!v)throw new AssertionError(why);}
 private String hex(byte[] b){StringBuilder s=new StringBuilder();for(byte v:b)s.append(String.format("%02x",v&255));return s.toString();}
 private byte[] bytes(ByteBuffer b){byte[] a=new byte[b.remaining()];b.get(a);return a;}
 private String sha(byte[] b)throws Exception{return hex(MessageDigest.getInstance("SHA-256").digest(b));}
 @Override public void onCreate(Bundle b){super.onCreate(b);start();}
 @Override public void onStart(){Bundle result=new Bundle();try{
  File files=getTargetContext().getFilesDir();byte[] state=Files.readAllBytes(new File(files,"source-world-test.state").toPath());
  List<String> frames=Files.readAllLines(new File(files,"source-world-frames.txt").toPath());
  List<String> lines=Files.readAllLines(new File(files,"source-world-packets.txt").toPath());Map<Long,String[]> expected=new HashMap<>();for(String line:lines){String[] t=line.split(" ");expected.put(Long.parseLong(t[0]),t);}
  int count=0,boundCount=0,wholeBound=0,splitBound=0;Set<Long> boundOwners=new HashSet<>();long pcmFrames=0;Set<Long> seen=new HashSet<>();long[] last=null;byte[] retained=null;String retainedHash=null;
  ByteBuffer pixels=ByteBuffer.allocateDirect(NativeCore.FRAME_BYTES);short[] pcm=new short[8192];MessageDigest sound=MessageDigest.getInstance("SHA-256");
  NativeCore core=new NativeCore(new File(files,"source-world-test.gba").getAbsolutePath());
  try{
   ok(!core.captureSourceWorld(true),"Source collection without capture accepted");
   ok(core.loadCheckpoint(state)&&core.capture(true)&&core.captureLayers(true)&&core.captureSourceWorld(true),"Source capture enable");
   long initial=core.timing()[2];
   for(int i=0;i<600;i++){
    ok(core.step(1|(i>=60&&i<120?16:0)|(i>=480&&i<540?32:0))==1,"Step "+i);
    ok(core.frame(pixels),"Frame copy");pixels.position(0);MessageDigest picture=MessageDigest.getInstance("SHA-256");picture.update(pixels);ok(hex(picture.digest()).equals(frames.get(i)),"Original frame "+i);
    long[] clock=core.timing();ok(clock[0]==16777216&&clock[1]==280896&&clock[2]==initial+i+1&&clock[3]==i+1,"Original timing");
    int amount;while((amount=core.audio(pcm))>0){pcmFrames+=amount;byte[] bytes=new byte[amount*4];for(int j=0;j<amount*2;j++){bytes[j*2]=(byte)pcm[j];bytes[j*2+1]=(byte)(pcm[j]>>8);}sound.update(bytes);}
    byte[] displayRaw=core.capturedScene(),boundRaw=core.capturedSourceScene();
    if(displayRaw==null)ok(boundRaw==null,"Source binding without display owner");
    else{
     ok(boundRaw!=null,"Source display binding missing at step "+i);NativeSceneSnapshot display=new NativeSceneSnapshot(displayRaw),bound=new NativeSceneSnapshot(boundRaw);
     ok(bound.epoch==display.epoch&&bound.refresh==display.refresh&&bound.kind==display.kind&&bound.splitRow==display.splitRow,"Display owner changed");
     ok(Arrays.equals(bytes(bound.packedLayers()),bytes(display.packedLayers()))&&Arrays.equals(bytes(bound.provenance()),bytes(display.provenance())),"Historical layers/provenance changed");
     for(int j=0;j<bound.geometryCount();j++){NativeScenePacket part=bound.geometry(j);if(boundOwners.add(part.serial)){String[] ref=expected.get(part.serial);ok(ref!=null&&sha(bytes(part.data())).equals(ref[2]),"Bound source geometry mismatch");}}
     boundCount++;if(bound.kind==1)wholeBound++;else splitBound++;
    }
    long[] info=core.captureStats();if(info[6]==0||seen.contains(info[7]))continue;
    byte[] old=core.capturedPacket();ByteBuffer header=ByteBuffer.wrap(old).order(ByteOrder.LITTLE_ENDIAN);long serial=header.getInt(16)&0xffffffffL,begin=header.getInt(20)&0xffffffffL,end=header.getInt(24)&0xffffffffL;
    byte[] raw=core.capturedSourceWorld(info[1],serial,begin,end);ok(raw!=null,"Missing source packet "+serial);String[] ref=expected.get(serial);ok(ref!=null&&raw.length==Integer.parseInt(ref[1])&&sha(raw).equals(ref[2]),"PC packet mismatch "+serial);
    last=new long[]{info[1],serial,begin,end};if(retained==null){retained=raw;retainedHash=sha(raw);}seen.add(serial);count++;
   }
   ok(count==148&&count==expected.size(),"Packet count");ok(boundCount==594&&wholeBound>0&&splitBound>0&&boundOwners.size()==148,"Bound display scope "+boundCount+" owners "+boundOwners.size());
   ok(pcmFrames==443007&&hex(sound.digest()).equals("eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e"),"Original audio");
   long[] key=last;AtomicReference<Throwable> problem=new AtomicReference<>();Thread wrong=new Thread(()->{try{core.capturedSourceScene();problem.set(new AssertionError("Wrong thread accepted"));}catch(IllegalStateException expectedFailure){}});wrong.start();wrong.join();ok(problem.get()==null,"Owner guard");
   ok(core.capturedSourceWorld(key[0]+1,key[1],key[2],key[3])==null&&core.capturedSourceWorld(key[0],-1,key[2],key[3])==null&&core.capturedSourceWorld(key[0],key[1],key[2],0x100000000L)==null,"Malformed identity guards");
   ok(core.loadCheckpoint(state)&&core.capturedSourceWorld(key[0],key[1],key[2],key[3])==null&&core.capturedSourceScene()==null,"Stale epoch");
   ok(core.captureSourceWorld(false)&&core.capturedSourceWorld(key[0],key[1],key[2],key[3])==null&&core.capturedSourceScene()==null,"Disabled capture");
  }finally{core.close();}
  ok(retained!=null&&sha(retained).equals(retainedHash),"Owned bytes changed after core close");
  JSONObject report=new JSONObject();report.put("result","PASS_ANDROID_SOURCE_DISPLAY_JNI");report.put("original_rgba_frames",600);report.put("original_timing",true);report.put("audio_pcm_frames",pcmFrames);report.put("pc_identical_source_packets",count);report.put("bound_display_snapshots",boundCount);report.put("whole_snapshots",wholeBound);report.put("split_snapshots",splitBound);report.put("bound_source_owners",boundOwners.size());report.put("historical_layers_provenance_unchanged",true);report.put("owner_and_identity_guards",true);report.put("epoch_and_disable_guards",true);report.put("owned_bytes_survive_close",true);report.put("diagnostic_environment_flags_required",false);report.put("api",Build.VERSION.SDK_INT);report.put("live_gpu_rendering",false);report.put("real_time_pacing",false);
  try(FileOutputStream file=getTargetContext().openFileOutput("source-world-jni-report.json",Context.MODE_PRIVATE)){file.write(report.toString(2).getBytes("UTF-8"));}
  result.putString("stream",report.toString());finish(Activity.RESULT_OK,result);
 }catch(Throwable failure){android.util.Log.e("NFSUGSourceWorld","Test failed",failure);result.putString("stream","FAIL: "+failure);finish(Activity.RESULT_CANCELED,result);}}
}
