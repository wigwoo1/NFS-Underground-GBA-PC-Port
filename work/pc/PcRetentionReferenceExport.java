package org.codex.nfsugpreview;
import java.nio.*;import java.nio.file.*;import java.io.*;import java.util.*;
public final class PcRetentionReferenceExport {
 static void le(DataOutputStream out,int v)throws Exception{out.writeInt(Integer.reverseBytes(v));}
 public static void main(String[]args)throws Exception{
  Path input=Paths.get(args[0]),output=Paths.get(args[1]);Files.createDirectories(output);int cases=0,cells=0;
  try(DirectoryStream<Path>files=Files.newDirectoryStream(input,"source-race-background-*.nrb")){for(Path file:files){NativeSceneSnapshot s=new NativeBackgroundScene(Files.readAllBytes(file)).sky.scene;int count=s.geometryCount();NativeRoadHistory[]roads=new NativeRoadHistory[count];NativeWallHistory[]walls=new NativeWallHistory[count];byte[][]proofs=new byte[count][];
   for(int o=0;o<count;o++){String stem="owner-"+s.geometry(o).serial;roads[o]=new NativeRoadHistory(Files.readAllBytes(input.resolve(stem+".nrh")));walls[o]=new NativeWallHistory(Files.readAllBytes(input.resolve(stem+".nwh")));proofs[o]=Files.readAllBytes(input.resolve(stem+".nrp"));}
   NativeRoadRetention rr=new NativeRoadRetention(s,roads,proofs);NativeWallRetention wr=new NativeWallRetention(s,walls,proofs);
   for(int o=0;o<count;o++)for(int kind=2;kind<=3;kind++){NativeScenePacket packet=s.geometry(o);int top=o==0?0:s.splitRow,bottom=count==1||o==1?160:s.splitRow;byte[]rgba=new byte[153600];
    if(kind==2){for(int i=0;i<rr.count();i++){NativeRoadRetention.Draw d=rr.draw(i);if(d.owner!=o)continue;ByteBuffer t=rr.texture(d);int[]r=d.records();for(int j=0;j<r.length;j+=3){int cell=r[j+1]*240+r[j];rgba[cell*4]=t.get(r[j+2]);rgba[cell*4+3]=(byte)255;}}}
    else{for(int i=0;i<wr.count();i++){NativeWallRetention.Draw d=wr.draw(i);if(d.owner!=o)continue;ByteBuffer t=wr.texture(d);int[]r=d.records();for(int j=0;j<r.length;j+=3){int cell=r[j+1]*240+r[j];rgba[cell*4]=t.get(r[j+2]);rgba[cell*4+3]=(byte)255;}}}
    NativeRoadHistory.Samples rs=kind==2?roads[o].samples(s.epoch,packet.endRefresh,packet.page):null;NativeWallHistory.Samples ws=kind==3?walls[o].samples(s.epoch,packet.endRefresh,packet.page):null;ByteBuffer proof=ByteBuffer.wrap(proofs[o]).order(ByteOrder.LITTLE_ENDIAN);ArrayList<Integer>records=new ArrayList<Integer>();
    for(int cell=0;cell<38400;cell++)if((rgba[cell*4+3]&255)!=0){int id=kind==2?roads[o].event(rs.event(cell)).assetKey-1:ws.asset(cell),offset=kind==2?rs.offset(cell):ws.offset(cell);records.add(cell);records.add(id);records.add(offset);records.add(proof.getInt(38480+cell*4));}
    try(DataOutputStream out=new DataOutputStream(Files.newOutputStream(output.resolve(s.refresh+"-"+o+"-"+kind+".ret")))){for(long v:new long[]{s.epoch,packet.serial,packet.beginRefresh,packet.endRefresh,packet.page})out.writeLong(v);out.writeInt(kind);out.writeInt(top);out.writeInt(bottom);out.writeInt(records.size()/4);out.write(rgba);for(int v:records)le(out,v);}cases++;cells+=records.size()/4;
   }
  }}if(cases!=34)throw new AssertionError("cases="+cases);System.out.println("PASS_PC_RETENTION_EXPORT cases="+cases+" cells="+cells);
 }
}
