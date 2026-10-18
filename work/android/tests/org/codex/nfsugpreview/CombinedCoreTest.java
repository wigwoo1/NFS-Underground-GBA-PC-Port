package org.codex.nfsugpreview;
import java.nio.*;import java.nio.file.*;import java.util.*;import java.util.zip.CRC32;
public final class CombinedCoreTest {
 static void check(boolean value){if(!value)throw new AssertionError();}
 public static void main(String[] args)throws Exception{
  List<String> refs=Files.readAllLines(Paths.get(args[2]));check(refs.size()==600);NativeSceneSnapshot[] retained=new NativeSceneSnapshot[2];int whole=0,split=0,missing=0;
  try(NativeCore core=new NativeCore(args[0])){
   check(core.loadCheckpoint(Files.readAllBytes(Paths.get(args[1])))&&core.captureSupported()&&core.capture(true)&&core.captureLayers(true));
   final boolean[] rejected={false};Thread t=new Thread(()->{try{core.capturedScene();}catch(IllegalStateException good){rejected[0]=true;}});t.start();t.join();check(rejected[0]);
   for(int i=0;i<600;i++){
    check(core.step(1|(i>=60&&i<120?16:i>=480&&i<540?32:0))==1);String[] expected=refs.get(i).split("\t");byte[] raw=core.capturedScene();
    if(raw==null){check(i<6&&Long.parseLong(expected[1])==0);missing++;continue;}
    CRC32 crc=new CRC32();crc.update(raw);check(raw.length==Long.parseLong(expected[1])&&crc.getValue()==Long.parseLong(expected[2]));
    NativeSceneSnapshot scene=new NativeSceneSnapshot(raw);check(scene.refresh==core.timing()[2]-1);Arrays.fill(raw,(byte)165);check(scene.data().getLong(0)==0x3142414eL);
    for(int row:new int[]{0,79,159}){ByteBuffer decoded=scene.row(row);check(Integer.toUnsignedLong(decoded.getInt(0))==scene.refresh&&decoded.getInt(4)==row);}
    if(retained[scene.kind-1]==null)retained[scene.kind-1]=scene;
    if(scene.kind==1)whole++;else split++;
   }
   check(whole==481&&split==113&&missing==6&&core.pause(true));long[] before=core.timing();for(int i=0;i<10;i++)check(core.step(1)==2&&Arrays.equals(before,core.timing()));check(core.pause(false));
   check(core.loadCheckpoint(Files.readAllBytes(Paths.get(args[1])))&&core.capturedScene()==null);
  }
  check(retained[0].row(159).getInt(4)==159&&retained[1].row(0).getInt(4)==0);
  System.out.println("PASS_COMBINED_SCENE_JNI snapshots=594 whole=481 split=113 initial_missing=6 crc_reference=true owner_guard=true retained_after_close=true state_invalidated=true");
 }
}
