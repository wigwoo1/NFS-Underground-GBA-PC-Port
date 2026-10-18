package org.codex.nfsugpreview;
import java.nio.*;import java.nio.file.*;import java.util.*;import java.lang.management.ManagementFactory;
public final class ValidatedBackgroundReuseTest {
 static volatile Object sink;
 static void ok(boolean b,String why){if(!b)throw new AssertionError(why);}
 static byte[] bytes(ByteBuffer b){byte[] out=new byte[b.remaining()];b.duplicate().get(out);return out;}
 static void same(ByteBuffer a,ByteBuffer b){ok(Arrays.equals(bytes(a),bytes(b)),"Buffer differs");}
 static void compare(NativeRetainedScene a,NativeRetainedScene b){
  ok(a.epoch==b.epoch&&a.refresh==b.refresh,"Endpoint differs");same(a.background.sky.scene.data(),b.background.sky.scene.data());same(a.background.exactRgba(),b.background.exactRgba());same(a.background.sky.exactRgba(),b.background.sky.exactRgba());same(a.prepared.paletteRgba(),b.prepared.paletteRgba());
  NativeSceneComposition x=a.prepared.composition,y=b.prepared.composition;ok(x.count()==y.count(),"Owner count");
  for(int o=0;o<x.count();o++){NativeSceneDrawPlan p=x.plan(o),q=y.plan(o);ok(p.count()==q.count(),"Draw count");for(int i=0;i<p.count();i++){
   NativeSceneDrawPlan.Draw d=p.draw(i),e=q.draw(i);ok(d.index==e.index&&d.width==e.width&&d.height==e.height&&d.vertices==e.vertices&&d.model==e.model&&d.indexed==e.indexed&&d.wall==e.wall,"Draw metadata");FloatBuffer f=d.mesh(),g=e.mesh();ok(f.remaining()==g.remaining(),"Mesh size");while(f.hasRemaining())ok(Float.floatToRawIntBits(f.get())==Float.floatToRawIntBits(g.get()),"Mesh bits");ok((d.lighting==null)==(e.lighting==null),"Lighting kind");for(int n=0;n<(d.lighting==null?1:16);n++)same(d.lighting==null?d.image():d.lighting.variant(n),e.lighting==null?e.image():e.lighting.variant(n));
  }}
  ok(a.roads.count()==b.roads.count()&&a.roads.cells()==b.roads.cells(),"Road retention size");for(int i=0;i<a.roads.count();i++){NativeRoadRetention.Draw d=a.roads.draw(i),e=b.roads.draw(i);ok(d.owner==e.owner&&d.event==e.event&&d.top==e.top&&d.bottom==e.bottom&&Arrays.equals(d.records(),e.records()),"Road proof");same(a.roads.texture(d),b.roads.texture(e));}
  ok(a.walls.count()==b.walls.count()&&a.walls.cells()==b.walls.cells(),"Wall retention size");for(int i=0;i<a.walls.count();i++){NativeWallRetention.Draw d=a.walls.draw(i),e=b.walls.draw(i);ok(d.owner==e.owner&&d.event==e.event&&d.top==e.top&&d.bottom==e.bottom&&Arrays.equals(d.records(),e.records()),"Wall proof");same(a.walls.texture(d),b.walls.texture(e));}
 }
 static NativeSourceSceneBinding.Source provider(Path dir,String suffix,Map<String,byte[]> inputs){return(e,s,b,f)->{String name="owner-"+s+suffix;try{if(!inputs.containsKey(name))inputs.put(name,Files.readAllBytes(dir.resolve(name)));return inputs.get(name);}catch(Exception failure){throw new RuntimeException(failure);}};}
 static int checked=0,missing=0,forged=0;
 static void check(byte[] raw,NativeSourceSceneBinding.Source world,NativeSourceSceneBinding.Source road,NativeSourceSceneBinding.Source wall,NativeSourceSceneBinding.Source proof){
  NativeSourceBackgroundBinding.Bound bound=NativeSourceBackgroundBinding.bindPrepared(raw,new NativeSourceSceneBinding(),world);ok(bound!=null,"Missing binding");NativeRetainedScene legacy=NativeRetainedScene.capture(bound.bytes,road,wall,proof),reuse=NativeRetainedScene.capturePrepared(bound,road,wall,proof,null);ok(reuse.background==bound.background,"Validated object reparsed");compare(legacy,reuse);
  ok(NativeSourceBackgroundBinding.bindPrepared(raw,new NativeSourceSceneBinding(),(e,s,b,f)->null)==null,"Missing world source accepted");
  try{NativeSourceBackgroundBinding.bindPrepared(raw,new NativeSourceSceneBinding(),(e,s,b,f)->{byte[] bad=world.packet(e,s,b,f).clone();ByteBuffer v=ByteBuffer.wrap(bad).order(ByteOrder.LITTLE_ENDIAN);v.putInt(16,v.getInt(16)+1);return bad;});throw new AssertionError("Forged world owner accepted");}catch(IllegalArgumentException expected){}
  ok(NativeRetainedScene.capturePrepared(bound,(e,s,b,f)->null,wall,proof,null)==null,"Missing road accepted");ok(NativeRetainedScene.capturePrepared(bound,road,(e,s,b,f)->null,proof,null)==null,"Missing wall accepted");ok(NativeRetainedScene.capturePrepared(bound,road,wall,(e,s,b,f)->null,null)==null,"Missing proof accepted");missing+=3;
  try{NativeRetainedScene.capturePrepared(bound,road,wall,(e,s,b,f)->{byte[] bad=proof.packet(e,s,b,f).clone();ByteBuffer.wrap(bad).order(ByteOrder.LITTLE_ENDIAN).putLong(24,e+1);return bad;},null);throw new AssertionError("Forged epoch accepted");}catch(IllegalArgumentException expected){forged++;}
  Arrays.fill(raw,(byte)0);Arrays.fill(bound.bytes,(byte)0);compare(legacy,reuse);checked++;
 }
 public static void main(String[] args)throws Exception{
  Path fixtures=Paths.get(args[0]),traffic=Paths.get(args[1]);Map<String,byte[]> inputs=new HashMap<>();NativeSourceSceneBinding.Source road=provider(fixtures,".nrh",inputs),wall=provider(fixtures,".nwh",inputs),proof=provider(fixtures,".nrp",inputs);
  try(DirectoryStream<Path> files=Files.newDirectoryStream(fixtures,"race-background-*.nrb")){for(Path path:files)check(Files.readAllBytes(path),(e,s,b,f)->{try{return Files.readAllBytes(fixtures.resolve("source-"+s+".nsp"));}catch(Exception failure){throw new RuntimeException(failure);}},road,wall,proof);}
  ok(checked==9,"Nine original fixtures required");
  byte[] raw=Files.readAllBytes(traffic.resolve("background.bin"));NativeSceneSnapshot original=new NativeBackgroundScene(raw).sky.scene;
  Map<String,byte[]> captured=new HashMap<>();for(String kind:new String[]{"world","road","wall","proof"})captured.put(kind,Files.readAllBytes(traffic.resolve("owner0-"+kind+".bin")));
  NativeSourceSceneBinding.Source world=(e,s,b,f)->captured.get("world"),r=(e,s,b,f)->captured.get("road"),w=(e,s,b,f)->captured.get("wall"),p=(e,s,b,f)->captured.get("proof");check(raw.clone(),world,r,w,p);
  NativeSourceBackgroundBinding.Bound bound=NativeSourceBackgroundBinding.bindPrepared(raw,new NativeSourceSceneBinding(),world);
  for(int i=0;i<5;i++){sink=NativeRetainedScene.capture(bound.bytes,r,w,p);sink=NativeRetainedScene.capturePrepared(bound,r,w,p,null);}
  com.sun.management.ThreadMXBean bean=(com.sun.management.ThreadMXBean)ManagementFactory.getThreadMXBean();ok(bean.isThreadAllocatedMemorySupported(),"Allocation accounting unavailable");bean.setThreadAllocatedMemoryEnabled(true);long thread=Thread.currentThread().getId(),oldBytes=0,newBytes=0,oldNs=0,newNs=0;
  for(int i=0;i<12;i++){for(int phase=0;phase<2;phase++){boolean old=(i+phase)%2==0;long bytes=bean.getThreadAllocatedBytes(thread),start=System.nanoTime();sink=old?NativeRetainedScene.capture(bound.bytes,r,w,p):NativeRetainedScene.capturePrepared(bound,r,w,p,null);long elapsed=System.nanoTime()-start,allocated=bean.getThreadAllocatedBytes(thread)-bytes;if(old){oldBytes+=allocated;oldNs+=elapsed;}else{newBytes+=allocated;newNs+=elapsed;}}}
  ok(oldBytes-newBytes>12L*1024*1024,"Expected redundant parse allocation reduction absent");
  System.out.println("{\"result\":\"PASS_VALIDATED_BACKGROUND_REUSE\",\"fixtures\":"+checked+",\"missing_histories_rejected\":"+missing+",\"forged_proof_epochs_rejected\":"+forged+",\"exact_scene_buffers_meshes_images_retention\":true,\"caller_mutation_isolated\":true,\"reused_background_identity\":true,\"benchmark_pairs\":12,\"legacy_allocated_bytes\":"+oldBytes+",\"reuse_allocated_bytes\":"+newBytes+",\"legacy_total_ns\":"+oldNs+",\"reuse_total_ns\":"+newNs+",\"host_microbenchmark_only\":true}");
 }
}
