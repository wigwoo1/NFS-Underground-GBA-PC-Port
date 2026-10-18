package org.codex.nfsugpreview;
import java.nio.*;import java.util.*;
/** Owned source-order corrected camera-space ring; projection is separate. */
final class NativeRoadClip {
 static double[][] clip(double[][] camera,ByteBuffer input,NativeRoadAttributes table){
  if(camera==null||camera.length<3||camera.length>32||input==null||input.remaining()!=288||table==null)throw new IllegalArgumentException("Corrected road ring inputs");ByteBuffer raw=input.slice().asReadOnlyBuffer().order(ByteOrder.LITTLE_ENDIAN);int count=camera.length,shift=raw.getInt(4),height=raw.getInt(8),affine=raw.getInt(12);
  if(raw.getInt(0)!=count||shift<0||shift>10||height<2||(height&1)!=0||affine<0||affine>1)throw new IllegalArgumentException("Corrected road source format");
  double offsetU=raw.getInt(24)/(256.0*(1<<shift)),offsetV=raw.getInt(28)/(256.0*height);double[][] result=new double[64][];int n=0;
  for(int i=0;i<count;i++){int previous=(i+count-1)%count;double[] a=camera[previous],b=camera[i];if(a==null||b==null||a.length<3||b.length<3)throw new IllegalArgumentException("Road camera point");for(int k=0;k<3;k++)if(!Double.isFinite(a[k])||!Double.isFinite(b[k]))throw new IllegalArgumentException("Nonfinite road point");boolean ai=a[2]>=64,bi=b[2]>=64;
   if(ai!=bi){int[] attributes={raw.getInt(32+previous*8),raw.getInt(36+previous*8),raw.getInt(32+i*8),raw.getInt(36+i*8)};double[] uv=table.near(a[2],b[2],attributes,shift,height,affine,64);double t=(64-a[2])/(b[2]-a[2]);result[n++]=new double[]{a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t,64,uv[0]+offsetU,uv[1]+offsetV};}
   if(bi){int[] attributes={raw.getInt(32+i*8),raw.getInt(36+i*8)};double[] uv=table.vertex(b[2],attributes,shift,height,affine);result[n++]=new double[]{b[0],b[1],b[2],uv[0]+offsetU,uv[1]+offsetV};}
  }return Arrays.copyOf(result,n);
 }
}
