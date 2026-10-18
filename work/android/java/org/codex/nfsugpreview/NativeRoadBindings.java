package org.codex.nfsugpreview;
import java.nio.*;import java.util.*;
/** Preflight source-owned road assets against immutable scene identities/order. */
final class NativeRoadBindings {
 static final class Candidate{
  private Candidate(long epoch,long serial,long begin,long end,int page,long[] identity){this.epoch=epoch;this.serial=serial;this.begin=begin;this.end=end;this.page=page;this.identity=identity.clone();this.bytes=null;}

  final long epoch,serial,begin,end;final int page;private final long[] identity;private final byte[] bytes;
  Candidate(long epoch,long serial,long begin,long end,int page,long[] identity,byte[] bytes){if(identity==null||identity.length!=5||bytes==null)throw new IllegalArgumentException("Road candidate");this.epoch=epoch;this.serial=serial;this.begin=begin;this.end=end;this.page=page;this.identity=identity.clone();this.bytes=bytes.clone();new NativeRoadAsset(this.bytes);}
 }
 static Candidate verifiedEmpty(long epoch,long serial,long begin,long end,int page,long[] identity,int[] proof){
  need(identity!=null&&identity.length==5&&identity[0]==1&&identity[3]==8&&identity[4]==0&&proof!=null&&proof.length==16);
  need(proof[0]==6&&proof[1]==1&&proof[2]==0&&proof[3]>=3&&proof[3]<=32&&proof[4]==1&&proof[5]==0&&proof[6]==0&&proof[7]==0);
  need(proof[8]>=0&&proof[8]<=proof[9]&&proof[9]<=240&&proof[10]>=0&&proof[10]<=proof[11]&&proof[11]<=160);
  need(epoch>0&&serial>=0&&serial<=0xffffffffL&&begin>=0&&end>=begin&&end<=0xffffffffL&&(page==0||page==1));
  return new Candidate(epoch,serial,begin,end,page,identity);
 }
 static final class Binding{
  final int owner,command,top,bottom;final boolean empty;final NativeRoadAsset asset;final NativeRoadEdgePlan plan;
  Binding(int owner,int command,int top,int bottom,NativeRoadAsset asset,NativeRoadEdgePlan plan){this.empty=asset==null;this.owner=owner;this.command=command;this.top=top;this.bottom=bottom;this.asset=asset;this.plan=plan;}
 }
 private final Binding[] bindings;private final NativeSceneSnapshot scene;
 private static void need(boolean b){if(!b)throw new IllegalArgumentException("Missing/conflicting road ownership");}
 NativeRoadBindings(NativeSceneSnapshot scene,Candidate[] candidates){
  need(scene!=null&&candidates!=null);this.scene=scene;ArrayList<Binding> bound=new ArrayList<Binding>();
  for(int owner=0;owner<scene.geometryCount();owner++){
   NativeScenePacket packet=scene.geometry(owner);NativeWorldScene world=new NativeWorldScene(packet);int[] reciprocal=new int[32768];ByteBuffer r=world.reciprocal();for(int i=0;i<reciprocal.length;i++)reciprocal[i]=r.getInt(i*4);
   for(int command=0;command<world.commandCount();command++){
    NativeWorldScene.Command c=world.command(command);if(c.model)continue;NativeWorldScene.Surface surface=world.surface(c.index);if(surface.kind!=1)continue;
    long[] identity=surface.identity();Candidate selected=null;boolean empty=false,nonempty=false;TreeMap<Long,Candidate> occurrences=new TreeMap<Long,Candidate>();
    for(Candidate candidate:candidates){need(candidate!=null);if(!Arrays.equals(identity,candidate.identity)||candidate.epoch!=scene.epoch||candidate.serial!=packet.serial||candidate.begin!=packet.beginRefresh||candidate.end!=packet.endRefresh||candidate.page!=packet.page)continue;
     selected=candidate;
     if(candidate.bytes==null){empty=true;continue;}nonempty=true;NativeRoadAsset asset=new NativeRoadAsset(candidate.bytes);need(asset.serial==packet.serial);
     for(int i=0;i<asset.spanCount;i++){long destination=Integer.toUnsignedLong(asset.span(i).getInt(0));int page=destination>=0x0600a000L?1:0;need(page==packet.page);}
     Candidate previous=occurrences.get(asset.ordinal);
     if(previous!=null){need(previous.bytes.length==candidate.bytes.length);for(int j=0;j<candidate.bytes.length;j++)if(j<12||j>=16)need(previous.bytes[j]==candidate.bytes[j]);}
     else occurrences.put(asset.ordinal,candidate);
    }
    need(selected!=null&&!(empty&&nonempty));
    if(nonempty){
     // Repeated full identities are separate original draw occurrences. Match
     // ordered command occurrences to recorded ordinals; never use screen bounds.
     int rank=0,total=0;
     for(int j=0;j<world.commandCount();j++){NativeWorldScene.Command other=world.command(j);if(other.model)continue;NativeWorldScene.Surface item=world.surface(other.index);if(item.kind==1&&Arrays.equals(identity,item.identity())){if(j<command)rank++;total++;}}
     need(occurrences.size()==total);selected=new ArrayList<Candidate>(occurrences.values()).get(rank);
    }
    NativeRoadAsset asset=selected.bytes==null?null:new NativeRoadAsset(selected.bytes);NativeDrawBounds bounds=NativeDrawBounds.command(world.bounds(),world.surfaceCount(),false,c.index);
    int top=owner==0?0:scene.splitRow,bottom=scene.geometryCount()==1||owner==1?160:scene.splitRow;
    bound.add(new Binding(owner,command,top,bottom,asset,asset==null?null:new NativeRoadEdgePlan(asset,reciprocal,bounds.right)));
   }
  }bindings=bound.toArray(new Binding[bound.size()]);
 }
 boolean belongsTo(NativeSceneSnapshot value){return scene==value;}
 int count(){return bindings.length;}Binding binding(int index){return bindings[index];}
}
