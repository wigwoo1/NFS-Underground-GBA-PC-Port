package org.codex.nfsugpreview;
import java.nio.*;import java.nio.file.*;
public class RoadEdgePlanTest{
 public static void main(String[] args)throws Exception{
  Path dir=Paths.get(args[0]);ByteBuffer input=ByteBuffer.wrap(Files.readAllBytes(dir.resolve("edge-reference.bin"))).order(ByteOrder.LITTLE_ENDIAN);int[] reciprocal=new int[32768];for(int i=0;i<32768;i++)reciprocal[i]=input.getInt();int files=input.getInt(),total=0;
  for(int i=0;i<files;i++){int nameBytes=input.getInt();byte[] name=new byte[nameBytes];input.get(name);NativeRoadAsset asset=new NativeRoadAsset(Files.readAllBytes(dir.resolve(new String(name,"UTF-8"))));int expected=input.getInt();NativeRoadEdgePlan plan=new NativeRoadEdgePlan(asset,reciprocal,238);if(plan.count()!=expected)throw new AssertionError("Edge count");int[] records=plan.records();for(int v:records)if(v!=input.getInt())throw new AssertionError("Edge address");if(records.length>0){records[0]=-1;if(plan.records()[0]<0)throw new AssertionError("Mutable plan");}total+=expected;}
  if(input.hasRemaining())throw new AssertionError("Trailing");System.out.println("PASS_ROAD_EDGE_PLAN assets="+files+" ordered_writes="+total);
 }
}
