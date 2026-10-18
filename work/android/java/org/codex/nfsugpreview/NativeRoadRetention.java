package org.codex.nfsugpreview;
import java.nio.*;import java.util.*;
/** Source-derived last-road ownership. Does not use measured screen coverage. */
final class NativeRoadRetention {
 static final class Draw{final int owner,event,top,bottom;private final int[] records;Draw(int owner,int event,int top,int bottom,int[] records){this.owner=owner;this.event=event;this.top=top;this.bottom=bottom;this.records=records;}int[] records(){return records.clone();}}
 private final NativeSceneSnapshot scene;private final NativeRoadHistory[] histories;private final Draw[] draws;private final int cells;
 private static void need(boolean b){if(!b)throw new IllegalArgumentException("Invalid retained road ownership");}
 NativeRoadRetention(NativeSceneSnapshot scene,NativeRoadHistory history,byte[][] proofs){
  this(scene,repeat(scene,history),proofs);
 }
 private static NativeRoadHistory[] repeat(NativeSceneSnapshot scene,NativeRoadHistory history){need(scene!=null&&history!=null);NativeRoadHistory[] result=new NativeRoadHistory[scene.geometryCount()];Arrays.fill(result,history);return result;}
 NativeRoadRetention(NativeSceneSnapshot scene,NativeRoadHistory[] histories,byte[][] proofs){
  need(scene!=null&&histories!=null&&histories.length==scene.geometryCount()&&proofs!=null&&proofs.length==scene.geometryCount());this.scene=scene;this.histories=histories.clone();for(NativeRoadHistory h:this.histories)need(h!=null&&h.epoch==scene.epoch);ArrayList<Draw> result=new ArrayList<Draw>();int total=0;
  for(int owner=0;owner<proofs.length;owner++){
   NativeRoadHistory history=this.histories[owner];NativeScenePacket packet=scene.geometry(owner);need(proofs[owner]!=null&&proofs[owner].length==192080);ByteBuffer b=ByteBuffer.wrap(proofs[owner].clone()).order(ByteOrder.LITTLE_ENDIAN);
   need(b.getLong(0)==0x3150524eL&&b.getLong(8)==1&&b.getLong(16)==192080&&b.getLong(24)==scene.epoch&&b.getLong(32)==packet.serial&&b.getLong(40)==packet.beginRefresh&&b.getLong(48)==packet.endRefresh&&b.getLong(56)==packet.endRefresh+1&&b.getLong(64)==packet.page&&b.getLong(72)==38400);
   NativeRoadHistory.Samples samples=history.samples(scene.epoch,packet.endRefresh,packet.page);ArrayList<ArrayList<Integer>> grouped=new ArrayList<ArrayList<Integer>>();for(int i=0;i<history.count();i++)grouped.add(new ArrayList<Integer>());// Compact runs sharing an exact immutable asset are safe to batch:
   // proof validation below assigns every cell once, so retained runs never overlap.
   int[] representative=new int[history.count()];HashMap<Integer,Integer> firstAsset=new HashMap<Integer,Integer>();for(int event=0;event<history.count();event++){int asset=history.event(event).assetKey;Integer first=firstAsset.get(asset);if(first==null){first=event;firstAsset.put(asset,first);}representative[event]=first;}
   int top=owner==0?0:scene.splitRow,bottom=proofs.length==1||owner==1?160:scene.splitRow;
   for(int cell=0;cell<38400;cell++){int kind=b.get(80+cell)&255;long refresh=Integer.toUnsignedLong(b.getInt(80+38400+cell*4));need(kind<=6&&(kind==0?refresh==0:refresh<=packet.endRefresh));if(kind!=1)continue;
    int event=samples.event(cell),offset=samples.offset(cell);need(event>=0&&offset>=0&&history.event(event).refresh==refresh&&offset<history.event(event).texture().remaining());int y=cell/240;if(y<top||y>=bottom)continue;
    ArrayList<Integer> values=grouped.get(representative[event]);values.add(cell%240);values.add(y);values.add(offset);total++;
   }
   for(int event=0;event<grouped.size();event++){ArrayList<Integer> values=grouped.get(event);if(values.isEmpty())continue;int[] records=new int[values.size()];for(int i=0;i<records.length;i++)records[i]=values.get(i);result.add(new Draw(owner,event,top,bottom,records));}
  }draws=result.toArray(new Draw[result.size()]);cells=total;
 }
 boolean belongsTo(NativeSceneSnapshot s){return scene==s;}int count(){return draws.length;}int cells(){return cells;}Draw draw(int index){return draws[index];}ByteBuffer texture(Draw draw){return histories[draw.owner].event(draw.event).texture();}
}
