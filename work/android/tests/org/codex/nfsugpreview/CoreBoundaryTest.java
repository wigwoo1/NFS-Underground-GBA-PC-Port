package org.codex.nfsugpreview;
import java.nio.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicReference;
public final class CoreBoundaryTest {
 static void ok(boolean x){if(!x)throw new AssertionError();}
 static String hex(byte[] bytes){StringBuilder s=new StringBuilder();for(byte b:bytes)s.append(String.format("%02x",b&255));return s.toString();}
 static String digest(ByteBuffer frame)throws Exception{
  byte[] bytes=new byte[NativeCore.FRAME_BYTES];frame.position(0);frame.get(bytes);
  for(int i=3;i<bytes.length;i+=4)ok(bytes[i]==(byte)255);
  return hex(MessageDigest.getInstance("SHA-256").digest(bytes));
 }
 public static void main(String[] args)throws Exception{
  byte[] state=Files.readAllBytes(Paths.get(args[1]));
  List<String> reference=Files.readAllLines(Paths.get(args[2]));
  ByteBuffer frame=ByteBuffer.allocateDirect(NativeCore.FRAME_BYTES);
  MessageDigest audio=MessageDigest.getInstance("SHA-256");
  int frames=0;long pcmFrames=0;
  NativeCore core=new NativeCore(args[0]);
  try{
   ok(!core.captureSupported()&&!core.capture(true)&&core.captureStats()==null&&core.capturedPacket()==null&&!core.captureLayers(true)&&core.capturedScene()==null);
   boolean rejected=false;try{new NativeCore(args[0]);}catch(IllegalStateException expected){rejected=true;}ok(rejected);
   ok(core.loadCheckpoint(state));
   long[] initial=core.timing();ok(initial[0]==16777216&&initial[1]==280896&&initial[3]==0);
   ok(!core.loadCheckpoint(new byte[state.length-1]));
   ok(!core.frame(ByteBuffer.allocate(NativeCore.FRAME_BYTES)));
   ok(!core.frame(frame.asReadOnlyBuffer()));
   ByteBuffer shortFrame=ByteBuffer.allocateDirect(32);for(int i=0;i<32;i++)shortFrame.put(i,(byte)77);
   ok(!core.frame(shortFrame));for(int i=0;i<32;i++)ok(shortFrame.get(i)==77);
   AtomicReference<Throwable> problem=new AtomicReference<>();
   Thread wrong=new Thread(()->{try{core.step(1);problem.set(new AssertionError("Wrong thread accepted"));}catch(IllegalStateException expected){}});
   wrong.start();wrong.join();ok(problem.get()==null);
   ok(Arrays.equals(initial,core.timing()));
   ok(core.pause(true));for(int i=0;i<10;i++)ok(core.step(1)==2);
   ok(Arrays.equals(initial,core.timing()));ok(core.pause(false));
   short[] samples=new short[8192];
   for(int i=0;i<reference.size();i++){
    int keys=1|(i>=60&&i<120?16:i>=480&&i<540?32:0);
    ok(core.step(keys)==1);ok(core.frame(frame));
    ok(digest(frame).equals(reference.get(i)));
    long[] timing=core.timing();ok(timing[2]==initial[2]+i+1&&timing[3]==i+1);
    int n=core.audio(samples);ok(n>=0&&n<=4096);pcmFrames+=n;
    byte[] pcm=new byte[n*4];for(int j=0;j<n*2;j++){pcm[2*j]=(byte)samples[j];pcm[2*j+1]=(byte)(samples[j]>>8);}
    audio.update(pcm);frames++;
   }
   byte[] saved=core.checkpoint();List<String> later=new ArrayList<>();
   for(int i=0;i<20;i++){ok(core.step(33)==1);ok(core.frame(frame));later.add(digest(frame));}
   ok(core.loadCheckpoint(saved));
   for(String expected:later){ok(core.step(33)==1);ok(core.frame(frame));ok(digest(frame).equals(expected));}
   byte[] battery=core.battery();ok(battery!=null);
   ok(core.loadBattery(battery));ok(Arrays.equals(battery,core.battery()));
   int wrongSize=battery.length==512?8192:512;
   ok(!core.loadBattery(new byte[wrongSize]));ok(Arrays.equals(battery,core.battery()));
  }finally{core.close();}
  core.close();boolean closed=false;try{core.step(1);}catch(IllegalStateException expected){closed=true;}ok(closed);
  try(NativeCore reopened=new NativeCore(args[0])){
   ok(reopened.loadCheckpoint(state));
   for(int i=0;i<16;i++){ok(reopened.step(1)==1);ok(reopened.frame(frame));ok(digest(frame).equals(reference.get(i)));}
  }
  for(int size:new int[]{512,8192,32768,65536,131072}){
   try(NativeCore fresh=new NativeCore(args[0])){
    byte[] bytes=new byte[size];for(int i=0;i<size;i++)bytes[i]=(byte)(i*37+size/512);
    ok(fresh.loadBattery(bytes));ok(Arrays.equals(bytes,fresh.battery()));
    ok(!fresh.loadBattery(new byte[size-1]));ok(Arrays.equals(bytes,fresh.battery()));
   }
  }
  String hash=hex(audio.digest());
  ok(pcmFrames==443007);ok(hash.equals("eedce61302b062d825e9a26fa1d8399f0a7c29eaf4319e33a3d71eedd40be33e"));
  String report="{\"result\":\"PASS_JVM_JNI_HOST\",\"frames\":"+frames+",\"pcm_frames\":"+pcmFrames+",\"audio_sha256\":\""+hash+"\",\"thread_guard\":true,\"pause_guard\":true,\"state_replay_frames\":20,\"reopen_frames\":16,\"battery_sizes\":5,\"android_execution\":false}";
  Files.write(Paths.get(args[3]),report.getBytes("UTF-8"));System.out.println(report);
 }
}
