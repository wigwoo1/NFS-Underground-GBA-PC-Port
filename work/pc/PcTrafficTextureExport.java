package org.codex.nfsugpreview;
import java.nio.*;import java.nio.file.*;import java.io.*;
/** Offline texture inputs from an existing frozen repaired scene. No core or GPU. */
public final class PcTrafficTextureExport {
 static byte[] read(Path input,String name)throws Exception{return Files.readAllBytes(input.resolve(name));}
 static NativeSourceSceneBinding.Source provider(final Path input,final NativeSceneSnapshot original,final String kind){return (epoch,serial,begin,end)->{
  for(int i=0;i<original.geometryCount();i++){NativeScenePacket packet=original.geometry(i);if(original.epoch==epoch&&packet.serial==serial&&packet.beginRefresh==begin&&packet.endRefresh==end){try{return read(input,"owner"+i+"-"+kind+".bin");}catch(Exception e){throw new IllegalArgumentException(e);}}}
  throw new IllegalArgumentException("Frozen source identity not found");
 };}
 static void buffer(DataOutputStream out,ByteBuffer b)throws Exception{byte[] data=new byte[b.remaining()];b.duplicate().get(data);out.writeInt(data.length);out.write(data);}
 public static void main(String[] args)throws Exception{
  Path input=Paths.get(args[0]),output=Paths.get(args[1]);
  byte[] raw=read(input,"background.bin");NativeSceneSnapshot original=new NativeBackgroundScene(raw).sky.scene;
  byte[] rebound=NativeSourceBackgroundBinding.bind(raw,new NativeSourceSceneBinding(),provider(input,original,"world"));
  NativeRetainedScene retained=NativeRetainedScene.capture(rebound,provider(input,original,"road"),provider(input,original,"wall"),provider(input,original,"proof"));
  if(retained==null||retained.epoch!=2||retained.refresh!=15360)throw new AssertionError("Wrong repaired scene");
  if(!java.util.Arrays.equals(rebound,read(input,"source-background-retry.bin")))throw new AssertionError("Rebound source changed");
  NativeSceneComposition composition=retained.prepared.composition;int total=0;
  for(int owner=0;owner<composition.count();owner++)total+=composition.plan(owner).count();
  if(composition.count()!=1||total!=17)throw new AssertionError("Repaired scene identity changed");
  try(DataOutputStream out=new DataOutputStream(Files.newOutputStream(output,StandardOpenOption.CREATE_NEW))){
   out.writeInt(0x4e545831);out.writeLong(retained.epoch);out.writeLong(retained.refresh);out.writeInt(composition.count());out.writeInt(total);
   for(int owner=0;owner<composition.count();owner++){NativeSceneDrawPlan plan=composition.plan(owner);for(int i=0;i<plan.count();i++){
    NativeSceneDrawPlan.Draw d=plan.draw(i);out.writeInt(owner);out.writeInt(i);out.writeInt(d.index);out.writeInt(d.width);out.writeInt(d.height);out.writeBoolean(d.model);out.writeBoolean(d.indexed);out.writeBoolean(d.wall);out.writeBoolean(d.lighting!=null);
    int levels=d.lighting==null?1:16;out.writeInt(levels);for(int level=0;level<levels;level++)buffer(out,d.lighting==null?d.image():d.lighting.variant(level));
   }}
  }
  System.out.println("PASS_FROZEN_TRAFFIC_TEXTURE_EXPORT epoch=2 refresh=15360 owners=1 commands=17");
 }
}
