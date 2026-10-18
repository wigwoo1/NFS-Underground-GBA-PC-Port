package org.codex.nfsugpreview;
import java.nio.*;import java.util.*;
/** Immutable initial source background; uncovered cells remain transparent. */
final class NativeBackgroundScene {
 final NativeSkyScene sky;
 private final byte[][] indices,coverage;
 private static void require(boolean b){if(!b)throw new IllegalArgumentException("Invalid background scene");}
 NativeBackgroundScene(byte[] input){
  require(input!=null&&input.length>=128&&input.length<=66*1024*1024);
  byte[] owned=input.clone();ByteBuffer b=ByteBuffer.wrap(owned).order(ByteOrder.LITTLE_ENDIAN);
  require(b.getLong(0)==0x3142524eL&&b.getLong(8)==1&&b.getLong(16)==owned.length);
  require(b.getLong(64)==128);long size=b.getLong(72);require(size>=128&&size<=owned.length-128);
  sky=new NativeSkyScene(Arrays.copyOfRange(owned,128,128+(int)size));NativeSceneSnapshot s=sky.scene;
  require(b.getLong(24)==s.epoch&&b.getLong(32)==s.refresh&&b.getLong(40)==s.kind&&b.getLong(48)==s.splitRow&&b.getLong(56)==s.geometryCount());
  indices=new byte[s.geometryCount()][];coverage=new byte[indices.length][];long end=128+size;
  for(int i=0;i<indices.length;i++){
   long at=b.getLong(80+i*16),n=b.getLong(88+i*16);require(at==end&&n==76880&&n<=owned.length-end);int p=(int)at;NativeScenePacket g=s.geometry(i);
   require(b.getLong(p)==0x3147424eL&&b.getLong(p+8)==1&&b.getLong(p+16)==n&&b.getLong(p+24)==s.epoch&&b.getLong(p+32)==g.serial&&b.getLong(p+40)==g.beginRefresh&&b.getLong(p+48)==g.endRefresh&&b.getLong(p+56)==g.endRefresh+1&&b.getLong(p+64)==g.page&&b.getLong(p+72)==38400);
   indices[i]=Arrays.copyOfRange(owned,p+80,p+38480);coverage[i]=Arrays.copyOfRange(owned,p+38480,p+76880);
   boolean any=false;for(byte v:coverage[i]){require(v==0||v==1);any|=v==1;}require(any);end+=n;
  }
  require(end==owned.length&&b.getLong(112)==0&&b.getLong(120)==0);if(indices.length==1)require(b.getLong(96)==0&&b.getLong(104)==0);
 }
 ByteBuffer exactRgba(){
  ByteBuffer out=ByteBuffer.allocateDirect(153600),layer=sky.scene.packedLayers();
  for(int y=0;y<160;y++){
   int owner=sky.scene.kind==2&&y>=sky.scene.splitRow?1:0;
   int ref=layer.getShort(20512+(y*25+24)*2)&65535,palette=28512+ref*4096;
   for(int x=0;x<240;x++){int at=y*240+x;if(coverage[owner][at]==0){out.putInt(0);continue;}
    int color=layer.getShort(palette+(indices[owner][at]&255)*2)&65535;
    for(int c=0;c<3;c++){int v=(color>>(c*5))&31;out.put((byte)((v<<3)|(v>>2)));}out.put((byte)255);
   }
  }out.flip();return out.asReadOnlyBuffer();
 }
}
