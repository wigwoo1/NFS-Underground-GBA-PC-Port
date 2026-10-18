package org.codex.nfsugpreview;
import java.nio.*;import java.nio.file.*;import java.security.*;import java.util.*;
/** Fixed-work Android ART component benchmark; no core, Activity, audio or GPU. */
public final class AndroidBackgroundReuseBenchmark {
 static volatile NativeRetainedScene sink;
 static byte[] background;static final Map<String,byte[]> components=new HashMap<>();
 static final NativeSourceSceneBinding oldBinding=new NativeSourceSceneBinding(),newBinding=new NativeSourceSceneBinding();
 static NativeRetainedScene prepare(boolean reuse){
  NativeSourceBackgroundBinding.Bound b=NativeSourceBackgroundBinding.bindPrepared(background,reuse?newBinding:oldBinding,(e,s,begin,end)->components.get("world"));
  NativeSourceSceneBinding.Source road=(e,s,begin,end)->components.get("road"),wall=(e,s,begin,end)->components.get("wall"),proof=(e,s,begin,end)->components.get("proof");
  return reuse?NativeRetainedScene.capturePrepared(b,road,wall,proof,null):NativeRetainedScene.capture(b.bytes,road,wall,proof);
 }
 static void bytes(MessageDigest hash,ByteBuffer value){hash.update(value.duplicate());}
 static void number(MessageDigest hash,int value){hash.update((byte)(value>>24));hash.update((byte)(value>>16));hash.update((byte)(value>>8));hash.update((byte)value);}
 static String hex(byte[] raw){StringBuilder s=new StringBuilder();for(byte value:raw)s.append(String.format("%02x",value&255));return s.toString();}
 static String fingerprint(NativeRetainedScene scene)throws Exception{
  if(scene==null||scene.epoch!=2||scene.refresh!=15360||scene.prepared.composition.count()!=1)throw new AssertionError("Wrong scene endpoint");
  MessageDigest hash=MessageDigest.getInstance("SHA-256");bytes(hash,scene.background.sky.scene.data());bytes(hash,scene.background.exactRgba());bytes(hash,scene.background.sky.exactRgba());bytes(hash,scene.prepared.paletteRgba());
  NativeSceneDrawPlan plan=scene.prepared.composition.plan(0);number(hash,plan.count());if(plan.count()!=17)throw new AssertionError("Wrong command count");
  for(int i=0;i<plan.count();i++){NativeSceneDrawPlan.Draw d=plan.draw(i);for(int value:new int[]{d.index,d.width,d.height,d.vertices,d.model?1:0,d.indexed?1:0,d.wall?1:0})number(hash,value);FloatBuffer mesh=d.mesh();while(mesh.hasRemaining())number(hash,Float.floatToRawIntBits(mesh.get()));for(int level=0;level<(d.lighting==null?1:16);level++)bytes(hash,d.lighting==null?d.image():d.lighting.variant(level));}
  number(hash,scene.roads.count());for(int i=0;i<scene.roads.count();i++){NativeRoadRetention.Draw d=scene.roads.draw(i);for(int v:new int[]{d.owner,d.event,d.top,d.bottom})number(hash,v);for(int v:d.records())number(hash,v);bytes(hash,scene.roads.texture(d));}
  number(hash,scene.walls.count());for(int i=0;i<scene.walls.count();i++){NativeWallRetention.Draw d=scene.walls.draw(i);for(int v:new int[]{d.owner,d.event,d.top,d.bottom})number(hash,v);for(int v:d.records())number(hash,v);bytes(hash,scene.walls.texture(d));}
  return hex(hash.digest());
 }
 public static void main(String[] args)throws Exception{
  Path input=Paths.get(args[0]);background=Files.readAllBytes(input.resolve("background.bin"));StringBuilder inputHashes=new StringBuilder();
  for(String kind:new String[]{"world","road","wall","proof"}){byte[] data=Files.readAllBytes(input.resolve("owner0-"+kind+".bin"));components.put(kind,data);if(inputHashes.length()>0)inputHashes.append(',');inputHashes.append('"').append(kind).append("\":\"").append(hex(MessageDigest.getInstance("SHA-256").digest(data))).append('"');}
  String expected=fingerprint(prepare(false));if(!fingerprint(prepare(true)).equals(expected))throw new AssertionError("Initial byte parity");
  for(int i=0;i<3;i++){sink=prepare(false);sink=prepare(true);}
  long[] oldNs=new long[12],newNs=new long[12];
  for(int pair=0;pair<12;pair++)for(int phase=0;phase<2;phase++){
   boolean reuse=(pair+phase)%2==1;long start=System.nanoTime();NativeRetainedScene scene=prepare(reuse);long elapsed=System.nanoTime()-start;sink=scene;
   if(!fingerprint(scene).equals(expected))throw new AssertionError("Measured scene bytes differ");if(reuse)newNs[pair]=elapsed;else oldNs[pair]=elapsed;
  }
  System.out.println("{\"result\":\"PASS_ANDROID_FIXED_SCENE_BACKGROUND_REUSE\",\"baseline_ns\":"+Arrays.toString(oldNs)+",\"reuse_ns\":"+Arrays.toString(newNs)+",\"paired_rounds\":12,\"warmup_pairs\":3,\"scene_sha256\":\""+expected+"\",\"component_sha256\":{"+inputHashes+"},\"background_sha256\":\""+hex(MessageDigest.getInstance("SHA-256").digest(background))+"\",\"all_measured_scene_bytes_exact\":true,\"includes_binding_and_retained_preparation\":true,\"core_logic_steps\":0,\"gpu_calls\":0,\"audio_playback\":false,\"full_scene_60fps\":false,\"java_vm\":\""+System.getProperty("java.vm.name")+"\"}");
 }
}
