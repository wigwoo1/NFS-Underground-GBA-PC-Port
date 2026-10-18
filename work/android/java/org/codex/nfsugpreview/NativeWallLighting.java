package org.codex.nfsugpreview;
import java.nio.*;
/** Matches PC native wall shading; not the original quantized GBA columns. */
final class NativeWallLighting {
 private final double[] x,z,shade;
 private NativeWallLighting(double[] x,double[] z,double[] shade){this.x=x;this.z=z;this.shade=shade;}
 static NativeWallLighting camera(double[] inputX,double[] inputZ,double[] inputShade,double center,double scale){
  if(inputX==null||inputZ==null||inputShade==null||inputX.length!=2||inputZ.length!=2||inputShade.length!=2||!Double.isFinite(center)||!Double.isFinite(scale)||scale<=0)throw new IllegalArgumentException("Wall light inputs");
  double[] x=inputX.clone(),z=inputZ.clone(),shade=inputShade.clone();for(int i=0;i<2;i++)if(!Double.isFinite(x[i])||!Double.isFinite(z[i])||!Double.isFinite(shade[i])||shade[i]<0||shade[i]>15)throw new IllegalArgumentException("Wall light endpoints");
  if(z[0]<64&&z[1]<64)return null;
  for(int i=0;i<2;i++)if(z[i]<64){int other=1-i;double t=(64-z[i])/(z[other]-z[i]);x[i]+=(x[other]-x[i])*t;shade[i]+=(shade[other]-shade[i])*t;z[i]=64;}
  for(int i=0;i<2;i++){x[i]=center+scale*x[i]/z[i];if(!Double.isFinite(x[i])||x[i]<-32760||x[i]>32760||z[i]>32767)throw new IllegalArgumentException("Unsupported wall light range");}
  return new NativeWallLighting(x,z,shade);
 }
 static NativeWallLighting surface(NativeScenePacket packet,NativeWorldScene world,int index){
  NativeWorldScene.Surface s=world.surface(index);if(!s.lit||s.kind!=2||s.corners!=4)throw new IllegalArgumentException("Lit wall quad required");NativeWorldMesh mesh=new NativeWorldMesh(packet,world,index);DoubleBuffer points=mesh.cameraVertices();ByteBuffer model=NativeModelMesh.model(packet,0),lighting=s.lighting();
  return camera(new double[]{points.get(0),points.get(3)},new double[]{points.get(2),points.get(5)},new double[]{lighting.getInt(4),lighting.getInt(8)},model.getDouble(24),model.getDouble(40));
 }
 double[] endpoints(){return new double[]{x[0],x[1],z[0],z[1],shade[0],shade[1]};}
 int[] columns(int count){if(count<1||count>16384)throw new IllegalArgumentException("Wall shade width");int[] out=new int[count];
  if(shade[0]==shade[1]){int level=Math.max(0,Math.min(15,(int)Math.floor(shade[0]+1e-10)));java.util.Arrays.fill(out,level);return out;}
  for(int i=0;i<count;i++){double p=(i+.5)*240/count,t=x[1]==x[0]?.5:(p-x[0])/(x[1]-x[0]);t=Math.max(0,Math.min(1,t));double a=(1-t)/z[0],b=t/z[1],value=(a*shade[0]+b*shade[1])/(a+b);out[i]=Math.max(0,Math.min(15,(int)Math.floor(value+1e-10)));}return out;
 }
}
