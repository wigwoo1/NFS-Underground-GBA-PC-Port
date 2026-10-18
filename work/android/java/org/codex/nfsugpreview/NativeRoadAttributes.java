package org.codex.nfsugpreview;
import java.nio.*;
/** Source UV correction: exact 32-bit wraps and continuous depth-cell extension. */
final class NativeRoadAttributes {
 private final ByteBuffer table;
 NativeRoadAttributes(ByteBuffer input){if(input==null||input.remaining()!=32768*4)throw new IllegalArgumentException("Road reciprocal table");byte[] owned=new byte[input.remaining()];input.duplicate().get(owned);table=ByteBuffer.wrap(owned).asReadOnlyBuffer().order(ByteOrder.LITTLE_ENDIAN);}
 private long reciprocal(int depth){return Integer.toUnsignedLong(table.getInt(depth*4));}
 private static void format(int shift,int height,int affine){if(shift<0||shift>10||height<2||(height&1)!=0||affine<0||affine>1)throw new IllegalArgumentException("Road source format");}
 private double[] project(int depth,int[] attributes,int shift,int height,int affine){
  format(shift,height,affine);if(depth<1||depth>=32768)throw new IllegalArgumentException("Road source depth");long r=reciprocal(depth);if(r==0)throw new IllegalArgumentException("Missing road reciprocal");double[] result=new double[2];
  for(int k=0;k<2;k++){int scaled=k==0?attributes[k]<<shift:attributes[k]*height;int word=affine==1?scaled<<1:(int)(((long)(scaled>>7)*r)>>8);double denominator=k==0?(1<<shift)*.5:height*.5;result[k]=(double)word/(affine==1?65536.0:(double)r)/denominator;}return result;
 }
 double[] vertex(double depth,int[] attributes,int shift,int height,int affine){
  if(attributes==null||attributes.length<2||!Double.isFinite(depth)||depth<1||depth>32767)throw new IllegalArgumentException("Road vertex attributes");int lo=(int)Math.floor(depth);double t=depth-lo;double[] a=project(lo,attributes,shift,height,affine);if(t==0)return a;double[] b=project(lo+1,attributes,shift,height,affine);return new double[]{a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t};
 }
 private double[] nearInteger(int z0,int z1,int[] attributes,int shift,int height,int affine,int near){
  boolean start=z0<near||(z0==near&&z1>=near);int behind=start?z0:z1,front=start?z1:z0,delta=front-behind;
  if(behind>near||front<near||delta<0||delta>=32768||near<1||near>=32768)throw new IllegalArgumentException("Road crossing range");if(reciprocal(near)==0)throw new IllegalArgumentException("Missing near reciprocal");long factor=((long)(near-behind)*reciprocal(delta))&0xffffffffL;int[] clipped=new int[2];
  for(int k=0;k<2;k++){int difference=attributes[k+2]-attributes[k];int adjustment=(int)(((long)difference*factor)>>24);clipped[k]=attributes[(start?0:2)+k]+(start?adjustment:-adjustment);}return project(near,clipped,shift,height,affine);
 }
 double[] near(double z0,double z1,int[] attributes,int shift,int height,int affine,int near){
  if(attributes==null||attributes.length<4||!Double.isFinite(z0)||!Double.isFinite(z1)||z0<-32768||z0>32767||z1<-32768||z1>32767||!((z0<near&&z1>=near)||(z1<near&&z0>=near)))throw new IllegalArgumentException("Road near attributes");format(shift,height,affine);
  int a=(int)Math.floor(z0),b=(int)Math.floor(z1);double tx=z0-a,ty=z1-b;double[] result=new double[2];
  for(int i=0;i<2;i++)for(int k=0;k<2;k++){double weight=(i==1?tx:1-tx)*(k==1?ty:1-ty);if(weight==0)continue;double[] corner=nearInteger(a+i,b+k,attributes,shift,height,affine,near);for(int channel=0;channel<2;channel++)result[channel]+=weight*corner[channel];}return result;
 }
}
