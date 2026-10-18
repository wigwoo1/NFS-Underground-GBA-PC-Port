package org.codex.nfsugpreview;
import java.nio.*;
/** Current-pose world mesh. Source-corrected road clipping is a separate gate. */
final class NativeWorldMesh {
 final NativeWorldScene.Surface surface;final int triangleVertices;final boolean affine;
 private final FloatBuffer vertices;private final DoubleBuffer camera;
 private static void need(boolean b){if(!b)throw new IllegalArgumentException("Invalid/unsupported world mesh");}
 private static double cross(double[] a,double[] b,double[] c){return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);}
 NativeWorldMesh(NativeScenePacket packet,NativeWorldScene world,int index){
  surface=world.surface(index);affine=surface.mode==4||surface.mode==6||surface.mode==10;boolean sourceCamera=surface.sourceCamera()!=null;NativeRoadCamera rawCamera=sourceCamera?new NativeRoadCamera(surface.sourceCamera()):null;if(sourceCamera){need(cxIntegerCompatible(packet,world));}
  ByteBuffer model=NativeModelMesh.model(packet,0);need(model.remaining()>=160);double cx=model.getDouble(24),cy=model.getDouble(32),scale=model.getDouble(40);need(Double.isFinite(cx)&&Double.isFinite(cy)&&Double.isFinite(scale)&&scale>0);double[] pose=NativeModelMesh.pose(model,48);
  for(int i=1;i<world.modelCount;i++){ByteBuffer other=NativeModelMesh.model(packet,i);need(other.remaining()>=104);for(int at=24;at<104;at++)need(other.get(at)==model.get(at));}
  int count=surface.corners;ByteBuffer points=surface.vertices(),uv=surface.uv();double[][] in=new double[count][5];double[] cameraValues=new double[count*3];
  for(int i=0;i<count;i++){double[] v={points.getDouble(i*24)-pose[0],points.getDouble(i*24+8)-pose[1],points.getDouble(i*24+16)-pose[2]};v=sourceCamera?rawCamera.point(new double[]{points.getDouble(i*24),points.getDouble(i*24+8),points.getDouble(i*24+16)}):NativeModelMesh.rotate(pose,v);for(int j=0;j<3;j++){need(Double.isFinite(v[j]));cameraValues[i*3+j]=v[j];}in[i]=new double[]{v[0],v[1],v[2],uv.getDouble(i*16),uv.getDouble(i*16+8)};}
  camera=DoubleBuffer.wrap(cameraValues).asReadOnlyBuffer();double[][] clipped=new double[64][5];int n=0;
  for(int i=0;!sourceCamera&&i<count;i++){double[] a=in[(i+count-1)%count],b=in[i];boolean ai=a[2]>=64,bi=b[2]>=64;if(ai!=bi){double t=(64-a[2])/(b[2]-a[2]);double[] v=new double[5];for(int j=0;j<5;j++)v[j]=a[j]+(b[j]-a[j])*t;v[2]=64;clipped[n++]=v;}if(bi)clipped[n++]=b;}
  if(!sourceCamera&&surface.sourceAttributes()!=null){clipped=NativeRoadClip.clip(in,surface.sourceAttributes(),new NativeRoadAttributes(world.reciprocal()));n=clipped.length;}
  double[][] sourceRing=null;if(sourceCamera){double[][] worldPoints=new double[count][3];for(int i=0;i<count;i++)for(int k=0;k<3;k++)worldPoints[i][k]=points.getDouble(i*24+k*8);sourceRing=new NativeRoadProjection(world.reciprocal()).ring(worldPoints,surface.sourceAttributes(),rawCamera,new int[]{(int)cx,(int)cy,(int)scale});n=sourceRing.length;}
  double[][] projected=new double[n][6];double area=0;int[] ids=new int[n];
  for(int i=0;i<n;i++){if(sourceCamera){double[] p=sourceRing[i];need(p[2]>0);ByteBuffer raw=surface.sourceAttributes();double z=16777216.0/p[2],r=affine?65536:p[2],u=p[3]/(r*surface.width*.5)+raw.getInt(24)/(256.0*surface.width),v=p[4]/(r*surface.height)+raw.getInt(28)/(512.0*surface.height);projected[i]=new double[]{p[0],p[1],z,u,v,1/z};}else{double[] v=clipped[i];double q=1/v[2];projected[i]=new double[]{cx+scale*v[0]*q,cy+scale*v[1]*q,v[2],v[3],v[4],q};}ids[i]=i;}
  for(int i=0;i<n;i++)area+=projected[i][0]*projected[(i+1)%n][1]-projected[(i+1)%n][0]*projected[i][1];need(Double.isFinite(area));double sign=area>=0?1:-1;float[] output=new float[62*3*5];int used=0,remaining=n;
  while(remaining>=3){boolean found=false;for(int j=0;j<remaining;j++){int prev=(j+remaining-1)%remaining,next=(j+1)%remaining;double[] a=projected[ids[prev]],b=projected[ids[j]],c=projected[ids[next]];if(cross(a,b,c)*sign<1e-8)continue;boolean inside=false;
    for(int k=0;k<remaining;k++){if(k==prev||k==j||k==next)continue;double[] v=projected[ids[k]];if(cross(a,b,v)*sign>1e-8&&cross(b,c,v)*sign>1e-8&&cross(c,a,v)*sign>1e-8){inside=true;break;}}if(inside)continue;
    for(double[] v:new double[][]{a,b,c}){double q=affine?1:v[5];double[] attributes={v[0],v[1],v[3]*q,v[4]*q,q};for(double value:attributes){need(Double.isFinite(value)&&Math.abs(value)<=Float.MAX_VALUE);output[used++]=(float)value;}}
    for(int k=j;k+1<remaining;k++)ids[k]=ids[k+1];remaining--;found=true;break;
   }if(!found)break;
  }
  triangleVertices=used/5;FloatBuffer buffer=ByteBuffer.allocateDirect(used*4).order(ByteOrder.nativeOrder()).asFloatBuffer();buffer.put(output,0,used).position(0);vertices=buffer.asReadOnlyBuffer();
 }
 private static boolean cxIntegerCompatible(NativeScenePacket packet,NativeWorldScene world){ByteBuffer model=NativeModelMesh.model(packet,0);for(int at=24;at<=40;at+=8){double v=model.getDouble(at);if(!Double.isFinite(v)||v<Integer.MIN_VALUE||v>Integer.MAX_VALUE||v!=(int)v)return false;}return world.bounds().remaining()==0||world.bounds().getDouble(8)==0;}
 FloatBuffer vertices(){return vertices.asReadOnlyBuffer();}DoubleBuffer cameraVertices(){return camera.asReadOnlyBuffer();}
}
