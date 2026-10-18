package org.codex.nfsugpreview;
import java.nio.*;import java.nio.file.*;import java.io.*;
/** Original retained draw batches, including original immutable texture addresses. */
public final class PcRetainedSceneReferenceExport {
 static void draw(DataOutputStream out,int owner,int kind,int top,int bottom,ByteBuffer texture,int[] records)throws Exception{out.writeInt(owner);out.writeInt(kind);out.writeInt(top);out.writeInt(bottom);PcSceneReferenceExport.buffer(out,texture);out.writeInt(records.length*4);for(int v:records)out.writeInt(Integer.reverseBytes(v));}
 public static void main(String[]args)throws Exception{Path input=Paths.get(args[0]),output=Paths.get(args[1]);Files.createDirectories(output);int scenes=0,groups=0,cells=0;
  try(DirectoryStream<Path>files=Files.newDirectoryStream(input,"source-race-background-*.nrb")){for(Path file:files){NativeSceneSnapshot s=new NativeBackgroundScene(Files.readAllBytes(file)).sky.scene;int count=s.geometryCount();NativeRoadHistory[]roads=new NativeRoadHistory[count];NativeWallHistory[]walls=new NativeWallHistory[count];byte[][]proofs=new byte[count][];
   for(int o=0;o<count;o++){String stem="owner-"+s.geometry(o).serial;roads[o]=new NativeRoadHistory(Files.readAllBytes(input.resolve(stem+".nrh")));walls[o]=new NativeWallHistory(Files.readAllBytes(input.resolve(stem+".nwh")));proofs[o]=Files.readAllBytes(input.resolve(stem+".nrp"));}
   NativeRoadRetention rr=new NativeRoadRetention(s,roads,proofs);NativeWallRetention wr=new NativeWallRetention(s,walls,proofs);
   try(DataOutputStream out=new DataOutputStream(Files.newOutputStream(output.resolve(s.refresh+".edge")))){out.writeInt(rr.count()+wr.count());for(int i=0;i<rr.count();i++){NativeRoadRetention.Draw d=rr.draw(i);draw(out,d.owner,2,d.top,d.bottom,rr.texture(d),d.records());}for(int i=0;i<wr.count();i++){NativeWallRetention.Draw d=wr.draw(i);draw(out,d.owner,3,d.top,d.bottom,wr.texture(d),d.records());}}
   scenes++;groups+=rr.count()+wr.count();cells+=rr.cells()+wr.cells();
  }}if(scenes!=9||cells!=307441)throw new AssertionError();System.out.println("PASS_PC_RETAINED_DRAW_EXPORT scenes="+scenes+" groups="+groups+" cells="+cells);
 }
}
