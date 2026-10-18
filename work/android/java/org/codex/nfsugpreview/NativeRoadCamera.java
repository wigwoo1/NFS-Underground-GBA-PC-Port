package org.codex.nfsugpreview;
import java.nio.*;
/** Original Q14 road camera with continuous world-cell interpolation. */
final class NativeRoadCamera {
 private final int[] matrix=new int[12];
 NativeRoadCamera(ByteBuffer input){if(input==null||input.remaining()!=56)throw new IllegalArgumentException("Road camera size");ByteBuffer b=input.slice().order(ByteOrder.LITTLE_ENDIAN);if(b.getInt(0)!=1||(b.getInt(4)&3)!=0)throw new IllegalArgumentException("Road camera metadata");for(int i=0;i<12;i++)matrix[i]=b.getInt(8+i*4);}
 private double axis(int x,int z,int k){int a=x+matrix[9],b=z+matrix[11],v=a*matrix[k]+b*matrix[6+k];return (short)(v>>14);}
 double[] point(double[] p){if(p==null||p.length!=3)throw new IllegalArgumentException("Road point");for(double v:p)if(!Double.isFinite(v)||v<Integer.MIN_VALUE||v>Integer.MAX_VALUE-1.0)throw new IllegalArgumentException("Road point range");int x=(int)Math.floor(p[0]),z=(int)Math.floor(p[2]);double fx=p[0]-x,fz=p[2]-z;double[] r={0,p[1]+matrix[10],0};for(int i=0;i<2;i++)for(int j=0;j<2;j++){double w=(i!=0?fx:1-fx)*(j!=0?fz:1-fz);if(w==0)continue;r[0]+=w*axis(x+i,z+j,0);r[2]+=w*axis(x+i,z+j,2);}return r;}
}
