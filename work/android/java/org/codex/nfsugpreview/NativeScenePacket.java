package org.codex.nfsugpreview;
import java.nio.*;
/** Owned geometry packet only. Sky/HUD/coverage ownership is a separate dependency. */
final class NativeScenePacket {
 final long epoch,serial,beginRefresh,endRefresh;
 final int page,version;
 private final ByteBuffer bytes;
 private final int[] offsets=new int[5],sizes=new int[5];
 NativeScenePacket(long epoch,byte[] input){
  if(input==null||input.length<92||input.length>256*1024*1024)throw new IllegalArgumentException("Invalid scene size");
  byte[] owned=input.clone();ByteBuffer b=ByteBuffer.wrap(owned).order(ByteOrder.LITTLE_ENDIAN);
  if(b.getInt(0)!=0x3150534e||(b.getInt(4)!=1&&b.getInt(4)!=2)||b.getInt(8)!=owned.length||b.getInt(12)!=5)
   throw new IllegalArgumentException("Invalid native scene header");
  this.epoch=epoch;version=b.getInt(4);serial=Integer.toUnsignedLong(b.getInt(16));
  beginRefresh=Integer.toUnsignedLong(b.getInt(20));endRefresh=Integer.toUnsignedLong(b.getInt(24));page=b.getInt(28);
  if(endRefresh<beginRefresh||page<0||page>1)throw new IllegalArgumentException("Invalid native scene timing/page");
  long end=92;
  for(int i=0;i<5;i++){
   int at=32+i*12;long offset=Integer.toUnsignedLong(b.getInt(at+4)),size=Integer.toUnsignedLong(b.getInt(at+8));
   if(b.getInt(at)!=i+1||offset<end||offset>owned.length||size>owned.length-offset)
    throw new IllegalArgumentException("Invalid scene section");
   offsets[i]=(int)offset;sizes[i]=(int)size;end=offset+size;
  }
  if(end!=owned.length)throw new IllegalArgumentException("Invalid trailing scene data");
  bytes=b.asReadOnlyBuffer().order(ByteOrder.LITTLE_ENDIAN);
 }
 ByteBuffer data(){return bytes.asReadOnlyBuffer().order(ByteOrder.LITTLE_ENDIAN);}
 ByteBuffer section(int index){
  if(index<0||index>=5)throw new IllegalArgumentException("Section index");
  ByteBuffer b=data();b.position(offsets[index]);b.limit(offsets[index]+sizes[index]);
  return b.slice().asReadOnlyBuffer().order(ByteOrder.LITTLE_ENDIAN);
 }
}
