package org.codex.nfsugpreview;
import java.nio.*;import java.util.*;
/** Ordered original boundary writes expressed as source texture addresses, not colors. */
final class NativeRoadEdgePlan {
 private final int[] records;private final NativeRoadAsset owner;
 NativeRoadEdgePlan(NativeRoadAsset asset,int[] reciprocal,int right){
  if(asset==null||right<0||right>240)throw new IllegalArgumentException("Road boundary");
  owner=asset;ArrayList<Integer> values=new ArrayList<Integer>();int textureSize=asset.texture().remaining();
  for(int i=0;i<asset.spanCount;i++){
   ByteBuffer s=asset.span(i);int[] context=new int[16];for(int j=0;j<16;j++)context[j]=s.getInt(16+j*4);
   int[][] runs=s.getInt(8)==0x03003190?NativeRoadPerspective.plan(context,reciprocal,32).runs:new int[][]{context};
   int at=0,destination=s.getInt(0),base=destination>=0x0600a000?0x0600a000:0x06000000;
   for(int[] c:runs){int u=c[8],v=c[9];for(int k=0;k<c[7];k++,at++){
    u&=c[1];v&=c[2];long tex=2L*((u>>>16)+((long)(v>>>16)<<c[0]));
    for(int duplicate=0;duplicate<=s.getInt(12);duplicate++)for(int lane=0;lane<2;lane++){
     int dest=destination-base+at*2+duplicate*240+lane,x=dest%240,y=dest/240;if(y>=160||x<right)continue;
     if(tex+lane>=textureSize||tex<0)throw new IllegalArgumentException("Road boundary texture");
     values.add(x);values.add(y);values.add((int)tex+lane);
    }u+=c[10];v+=c[11];
   }}if(at!=s.getInt(4))throw new IllegalArgumentException("Road boundary run width");
  }
  records=new int[values.size()];for(int i=0;i<records.length;i++)records[i]=values.get(i);
 }
 boolean belongsTo(NativeRoadAsset asset){return owner==asset;}
 int count(){return records.length/3;}
 int[] records(){return records.clone();}
}
