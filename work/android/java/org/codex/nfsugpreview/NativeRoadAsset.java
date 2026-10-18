package org.codex.nfsugpreview;
import java.nio.*;import java.util.*;
/** Immutable NFRE original road spans/texture; mirrors camera/road_asset.h gates. */
final class NativeRoadAsset {
 final long serial,pass,ordinal,shift,source;final int spanCount;
 private final ByteBuffer data;private final int textureOffset,textureBytes;
 private static void need(boolean b){if(!b)throw new IllegalArgumentException("Invalid original road asset");}
 private static long word(ByteBuffer b,int at){return Integer.toUnsignedLong(b.getInt(at));}
 NativeRoadAsset(byte[] input){
  need(input!=null&&input.length>=40&&input.length<=1100000);byte[] owned=input.clone();ByteBuffer b=ByteBuffer.wrap(owned).order(ByteOrder.LITTLE_ENDIAN);
  long[] h=new long[10];for(int i=0;i<10;i++)h[i]=word(b,i*4);
  need(h[0]==0x4552464eL&&h[1]==1&&h[3]<4&&h[4]<144&&h[5]>0&&h[5]<=512&&h[6]<=15&&h[9]==40+h[5]*80&&h[8]<=1048576&&h[9]+h[8]==owned.length&&h[7]>=0x08000000L&&h[7]<0x0a000000L&&h[8]<=0x0a000000L-h[7]);
  long um=word(b,60),vm=word(b,64);need(((um|vm)&0x80000000L)==0);long extent=2*((um>>>16)+((vm>>>16)<<h[6])+1);need(extent<=1048576&&extent==h[8]);
  for(int i=0;i<h[5];i++){
   int at=40+i*80;long[] s=new long[20];for(int j=0;j<20;j++)s[j]=word(b,at+j*4);
   long page=s[0]>=0x0600a000L?0x0600a000L:0x06000000L,offset=s[0]-page;
   need(offset>=0&&offset<38400&&offset%240+s[1]*2<=242&&(s[2]==0x03003190L||s[2]==0x030056d8L));
   need(s[4]==h[6]&&s[9]==h[7]&&s[5]==um&&s[6]==vm&&s[10]==s[0]&&s[11]==s[1]&&s[1]>0&&s[1]<=121&&s[3]<=1&&s[0]>=0x06000000L&&s[0]<0x06014000L&&s[0]%2==0);
  }
  serial=h[2];pass=h[3];ordinal=h[4];spanCount=(int)h[5];shift=h[6];source=h[7];textureOffset=(int)h[9];textureBytes=(int)h[8];data=b.asReadOnlyBuffer().order(ByteOrder.LITTLE_ENDIAN);
 }
 ByteBuffer span(int index){if(index<0||index>=spanCount)throw new IllegalArgumentException("Road span index");return slice(40+index*80,80);}
 ByteBuffer texture(){return slice(textureOffset,textureBytes);}
 private ByteBuffer slice(int at,int n){ByteBuffer b=data.duplicate();b.position(at);b.limit(at+n);return b.slice().asReadOnlyBuffer().order(ByteOrder.LITTLE_ENDIAN);}
}
