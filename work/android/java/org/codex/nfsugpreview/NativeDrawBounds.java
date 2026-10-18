package org.codex.nfsugpreview;
import java.nio.*;
/** Source half-open bounds; same pixel-center rounding as PC packet_preview.c. */
final class NativeDrawBounds {
 final int left,right,top,bottom;
 NativeDrawBounds(int l,int r,int t,int b){if(l<0||l>r||r>240||t<0||t>b||b>160)throw new IllegalArgumentException("Draw bounds");left=l;right=r;top=t;bottom=b;}
 static NativeDrawBounds command(ByteBuffer bytes,int worldCount,boolean model,int index){
  if(bytes.remaining()==0||(model&&bytes.getInt(0)==0x3142464e))return new NativeDrawBounds(0,240,0,160);
  int at=16+(model?worldCount+index:index)*8;return new NativeDrawBounds(bytes.getShort(at)&65535,bytes.getShort(at+2)&65535,bytes.getShort(at+4)&65535,bytes.getShort(at+6)&65535);
 }
 int[] scissor(int width,int height){if(width<1||height<1||width>16384||height>16384)throw new IllegalArgumentException("Viewport bounds");int l=(int)Math.ceil(left*(width/240.0)-.5),r=(int)Math.ceil(right*(width/240.0)-.5),t=(int)Math.ceil(top*(height/160.0)-.5),b=(int)Math.ceil(bottom*(height/160.0)-.5);return new int[]{l,height-b,r-l,b-t};}
}
