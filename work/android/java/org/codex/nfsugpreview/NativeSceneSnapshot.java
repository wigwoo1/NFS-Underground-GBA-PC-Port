package org.codex.nfsugpreview;
import java.nio.*;
/** Immutable NAB1 geometry plus historical layers. No GPU/timing claim. */
final class NativeSceneSnapshot {
 final long epoch,refresh;final int kind,splitRow;
 private final ByteBuffer bytes;private final int[] offsets=new int[4],sizes=new int[4];
 private final NativeScenePacket[] packets;
 private static void require(boolean condition){if(!condition)throw new IllegalArgumentException("Invalid combined scene snapshot");}
 private static long u32(ByteBuffer b,int at){return Integer.toUnsignedLong(b.getInt(at));}
 private static ByteBuffer view(ByteBuffer b,int offset,int size){ByteBuffer v=b.asReadOnlyBuffer().order(ByteOrder.LITTLE_ENDIAN);v.position(offset);v.limit(offset+size);return v.slice().asReadOnlyBuffer().order(ByteOrder.LITTLE_ENDIAN);}
 NativeSceneSnapshot(byte[] input){
  require(input!=null&&input.length>=128&&input.length<=64*1024*1024);
  ByteBuffer b=ByteBuffer.wrap(input.clone()).order(ByteOrder.LITTLE_ENDIAN);
  require(b.getLong(0)==0x3142414eL&&b.getLong(8)==1&&b.getLong(16)==input.length);
  epoch=b.getLong(24);refresh=b.getLong(32);long k=b.getLong(40),cut=b.getLong(48),count=b.getLong(56);
  require(epoch>0&&refresh>=0&&refresh<=0xffffffffL&&((k==1&&cut==0&&count==1)||(k==2&&cut>0&&cut<160&&count==2)));
  kind=(int)k;splitRow=(int)cut;long end=128;
  for(int i=0;i<4;i++){long offset=b.getLong(64+i*16),size=b.getLong(72+i*16);require(offset==end&&size>=0&&size<=input.length-end);offsets[i]=(int)offset;sizes[i]=(int)size;end+=size;}
  require(end==input.length&&sizes[0]>=92&&(count==2?sizes[1]>=92:sizes[1]==0)&&sizes[3]==5312&&sizes[2]>=28512);
  packets=new NativeScenePacket[(int)count];
  for(int i=0;i<packets.length;i++){byte[] packet=new byte[sizes[i]];view(b,offsets[i],sizes[i]).get(packet);packets[i]=new NativeScenePacket(epoch,packet);}
  ByteBuffer layer=view(b,offsets[2],sizes[2]);long pages=u32(layer,16);
  require(u32(layer,0)==0x31504c4eL&&u32(layer,4)==1&&u32(layer,8)==sizes[2]&&u32(layer,12)==160&&pages>0&&pages<=4000&&u32(layer,20)==25&&u32(layer,24)==4096&&u32(layer,28)==refresh&&sizes[2]==28512+pages*4096);
  for(int y=0;y<160;y++){require(u32(layer,32+y*128)==refresh&&u32(layer,36+y*128)==y);for(int part=0;part<25;part++)require((layer.getShort(20512+(y*25+part)*2)&65535)<pages);}
  ByteBuffer provenance=view(b,offsets[3],sizes[3]);
  require(provenance.getLong(0)==epoch&&provenance.getLong(8)==refresh&&provenance.getLong(32)>0&&provenance.getLong(40)>0&&provenance.getLong(48)==160&&provenance.getLong(56)==1);
  long audit=provenance.getLong(40);
  for(int y=0;y<160;y++)require(provenance.getLong((24+y*4)*8)==(layer.getShort(32+y*128+8)&65535));
  if(kind==1){int matches=0;long selected=-1;
   for(int owner=0;owner<2;owner++){int at=(8+owner*8)*8;if(provenance.getLong(at+56)!=1||provenance.getLong(at)!=epoch||provenance.getLong(at+48)!=audit||provenance.getLong(at+24)>refresh)continue;
    long page=provenance.getLong(at+32),generation=provenance.getLong(at+40);if(page<0||page>1)continue;boolean match=true;
    for(int y=0;y<160;y++){int row=(24+y*4)*8;long control=provenance.getLong(row);if((control&7)!=4||(control&128)!=0||((control>>4)&1)!=page||provenance.getLong(row+8+(int)page*8)!=generation||provenance.getLong(row+24)!=audit){match=false;break;}}
    if(match){matches++;selected=provenance.getLong(at+8);}
   }require(matches==1&&selected==packets[0].serial);
  }else require(packets[0].serial<packets[1].serial&&packets[0].endRefresh<packets[1].endRefresh&&packets[1].endRefresh==refresh&&packets[0].page!=packets[1].page);
  for(int i=0;i<packets.length;i++){NativeScenePacket packet=packets[i];int found=-1;
   for(int owner=0;owner<2;owner++){int at=(8+owner*8)*8;if(provenance.getLong(at+56)==1&&provenance.getLong(at)==epoch&&provenance.getLong(at+8)==packet.serial){require(found==-1);found=at;}}
   require(found>=0&&provenance.getLong(found+16)==packet.beginRefresh&&provenance.getLong(found+24)==packet.endRefresh&&provenance.getLong(found+32)==packet.page&&provenance.getLong(found+48)==audit&&packet.endRefresh<=refresh);
   int begin=kind==1||i==0?0:splitRow,limit=kind==1||i==1?160:splitRow;long generation=provenance.getLong(found+40);
   for(int y=begin;y<limit;y++){int at=(24+y*4)*8;long control=provenance.getLong(at);require((control&7)==4&&(control&(kind==2?0x8080:0x80))==0&&((control>>4)&1)==packet.page&&provenance.getLong(at+8+packet.page*8)==generation&&provenance.getLong(at+24)==audit);}
  }
  bytes=b.asReadOnlyBuffer().order(ByteOrder.LITTLE_ENDIAN);
 }
 ByteBuffer data(){return bytes.asReadOnlyBuffer().order(ByteOrder.LITTLE_ENDIAN);}
 NativeScenePacket geometry(int index){if(index<0||index>=packets.length)throw new IllegalArgumentException("Geometry index");return packets[index];}
 int geometryCount(){return packets.length;}
 ByteBuffer packedLayers(){return view(bytes,offsets[2],sizes[2]);}
 ByteBuffer provenance(){return view(bytes,offsets[3],sizes[3]);}
 ByteBuffer row(int y){if(y<0||y>=160)throw new IllegalArgumentException("Row index");ByteBuffer layer=packedLayers();byte[] row=new byte[100480];view(layer,32+y*128,128).get(row,0,128);for(int part=0;part<25;part++){int ref=layer.getShort(20512+(y*25+part)*2)&65535;view(layer,28512+ref*4096,part==24?2048:4096).get(row,128+part*4096,part==24?2048:4096);}return ByteBuffer.wrap(row).asReadOnlyBuffer().order(ByteOrder.LITTLE_ENDIAN);}
}
