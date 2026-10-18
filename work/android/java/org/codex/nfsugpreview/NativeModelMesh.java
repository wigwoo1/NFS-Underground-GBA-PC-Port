package org.codex.nfsugpreview;
import java.nio.*;import java.util.*;
/** Diagnostic current-pose model mesh. World ordering/visibility/composition are separate. */
final class NativeModelMesh {
 final int width,height,sourceVertices,sourceFaces,triangleVertices;
 private final FloatBuffer triangles;private final DoubleBuffer camera;private final ByteBuffer rgba,indices;
 private static void need(boolean condition){if(!condition)throw new IllegalArgumentException("Invalid native model");}
 private static int bounded(ByteBuffer b,int at,int max){long n=Integer.toUnsignedLong(b.getInt(at));need(n>0&&n<=max);return (int)n;}
 private static double number(ByteBuffer b,int at){double v=b.getDouble(at);need(Double.isFinite(v));return v;}
 static double[] pose(ByteBuffer b,int at){double[] p=new double[7];for(int i=0;i<7;i++)p[i]=number(b,at+i*8);double n=Math.sqrt(p[3]*p[3]+p[4]*p[4]+p[5]*p[5]+p[6]*p[6]);need(Double.isFinite(n)&&n>=1e-10);for(int i=3;i<7;i++)p[i]/=n;return p;}
 static double[] rotate(double[] q,double[] v){double tx=2*(q[4]*v[2]-q[5]*v[1]),ty=2*(q[5]*v[0]-q[3]*v[2]),tz=2*(q[3]*v[1]-q[4]*v[0]);return new double[]{v[0]+q[6]*tx+q[4]*tz-q[5]*ty,v[1]+q[6]*ty+q[5]*tx-q[3]*tz,v[2]+q[6]*tz+q[3]*ty-q[4]*tx};}
 static int modelCount(NativeScenePacket packet){ByteBuffer b=packet.section(0);need(b.remaining()>=8);if(b.getInt(0)==0x324d464e)return 1;need(b.getInt(0)==0x314c4d4e);int n=bounded(b,4,16);need(n>=2);return n;}
 static ByteBuffer model(NativeScenePacket packet,int index){ByteBuffer b=packet.section(0);int n=modelCount(packet);need(index>=0&&index<n);if(n==1)return b;long end=8+n*8;need(end<=b.remaining());int chosen=0,size=0;
  for(int i=0;i<n;i++){long offset=Integer.toUnsignedLong(b.getInt(8+i*8)),bytes=Integer.toUnsignedLong(b.getInt(12+i*8));need(offset%8==0&&offset>=end&&offset<=b.remaining()&&bytes>=160&&bytes<=b.remaining()-offset);if(i==index){chosen=(int)offset;size=(int)bytes;}end=offset+bytes;}need(end==b.remaining());b.position(chosen);b.limit(chosen+size);return b.slice().asReadOnlyBuffer().order(ByteOrder.LITTLE_ENDIAN);
 }
 NativeModelMesh(ByteBuffer input){
  need(input!=null);ByteBuffer b=input.slice().order(ByteOrder.LITTLE_ENDIAN);need(b.remaining()>=160&&b.getInt(0)==0x324d464e);
  sourceVertices=bounded(b,4,2048);sourceFaces=bounded(b,8,512);int corners=bounded(b,12,4096);width=bounded(b,16,1024);height=bounded(b,20,1024);int pixels=width*height;
  long base=160L+sourceVertices*24L+sourceFaces+corners*18L+pixels*4L;need(base<=b.remaining());int trailer=b.remaining()-(int)base;
  need(trailer==0||(trailer==16+pixels&&b.getInt((int)base)==0x31495a4e&&b.getInt((int)base+4)==width&&b.getInt((int)base+8)==height&&b.getInt((int)base+12)==0));
  double cx=number(b,24),cy=number(b,32),scale=number(b,40);need(scale>0);double[] cam=pose(b,48),object=pose(b,104);double[][] points=new double[sourceVertices][3];double[] cameraValues=new double[sourceVertices*3];
  for(int i=0;i<sourceVertices;i++){double[] v={number(b,160+i*24),number(b,168+i*24),number(b,176+i*24)};v=rotate(object,v);for(int j=0;j<3;j++)v[j]+=object[j]-cam[j];v=rotate(cam,v);for(int j=0;j<3;j++){need(Double.isFinite(v[j]));cameraValues[i*3+j]=v[j];}points[i]=v;}
  camera=DoubleBuffer.wrap(cameraValues).asReadOnlyBuffer();int sizes=160+sourceVertices*24,ids=sizes+sourceFaces,uv=ids+corners*2,texture=uv+corners*16,total=0;
  for(int face=0;face<sourceFaces;face++){int n=b.get(sizes+face)&255;need(n>=3&&n<=32);total+=n;}need(total==corners);
  for(int i=0;i<corners;i++){need((b.getShort(ids+i*2)&65535)<sourceVertices);number(b,uv+i*16);number(b,uv+i*16+8);}
  float[] output=new float[sourceFaces*62*3*5];int used=0,corner=0;
  for(int face=0;face<sourceFaces;face++){int n=b.get(sizes+face)&255;double[][] ring=new double[n][5];for(int i=0;i<n;i++){double[] v=points[b.getShort(ids+(corner+i)*2)&65535];ring[i]=new double[]{v[0],v[1],v[2],b.getDouble(uv+(corner+i)*16),b.getDouble(uv+(corner+i)*16+8)};}corner+=n;
   double[][] clipped=new double[64][5];int count=0;for(int i=0;i<n;i++){double[] a=ring[(i+n-1)%n],v=ring[i];boolean ai=a[2]>=1,bi=v[2]>=1;if(ai!=bi){double t=(1-a[2])/(v[2]-a[2]);double[] c=new double[5];for(int j=0;j<5;j++)c[j]=a[j]+(v[j]-a[j])*t;c[2]=1;clipped[count++]=c;}if(bi)clipped[count++]=v;}
   if(count<3)continue;double[][] projected=new double[count][5];double area=0;
   for(int i=0;i<count;i++){double[] v=clipped[i];double q=1/v[2];projected[i]=new double[]{cx+scale*v[0]*q,cy+scale*v[1]*q,v[3]*q,v[4]*q,q};}
   for(int i=0;i<count;i++)area+=projected[i][0]*projected[(i+1)%count][1]-projected[(i+1)%count][0]*projected[i][1];need(Double.isFinite(area));if(area>=0)continue;
   for(int i=1;i<count-1;i++)for(int index:new int[]{0,i,i+1})for(double v:projected[index]){need(Double.isFinite(v)&&Math.abs(v)<=Float.MAX_VALUE);output[used++]=(float)v;}
  }
  triangleVertices=used/5;FloatBuffer floats=ByteBuffer.allocateDirect(used*4).order(ByteOrder.nativeOrder()).asFloatBuffer();floats.put(output,0,used).position(0);triangles=floats.asReadOnlyBuffer();
  ByteBuffer color=ByteBuffer.allocateDirect(pixels*4);ByteBuffer src=b.duplicate();src.position(texture);src.limit(texture+pixels*4);color.put(src).position(0);rgba=color.asReadOnlyBuffer();
  if(trailer!=0){ByteBuffer index=ByteBuffer.allocateDirect(pixels);src=b.duplicate();src.position((int)base+16);src.limit((int)base+16+pixels);index.put(src).position(0);indices=index.asReadOnlyBuffer();}else indices=null;
 }
 FloatBuffer vertices(){return triangles.asReadOnlyBuffer();}
 DoubleBuffer cameraVertices(){return camera.asReadOnlyBuffer();}
 ByteBuffer texture(){return rgba.asReadOnlyBuffer();}
 ByteBuffer originalIndices(){return indices==null?null:indices.asReadOnlyBuffer();}
}
