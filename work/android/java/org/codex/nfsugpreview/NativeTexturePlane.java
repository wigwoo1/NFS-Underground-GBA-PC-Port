package org.codex.nfsugpreview;
import java.nio.*;
/** Original screen-space texture planes, independent of raster edge snapping. */
final class NativeTexturePlane {
 final float x,y;final float[] base=new float[3],dx=new float[3],dy=new float[3];
 NativeTexturePlane(FloatBuffer vertices,int vertex){this(vertices,vertex,false);}
 NativeTexturePlane(FloatBuffer vertices,int vertex,boolean model){
  int at=vertex*5;if(vertex<0||at+15>vertices.limit())throw new IllegalArgumentException("Texture plane triangle");
  x=vertices.get(at);y=vertices.get(at+1);double bx=vertices.get(at+5)- (double)x,by=vertices.get(at+6)-(double)y,cx=vertices.get(at+10)-(double)x,cy=vertices.get(at+11)-(double)y;
  double det=bx*cy-by*cx,normal=vertices.get(at+4);
  if(!Double.isFinite(det)||det==0||!(normal>0)){
   if(!model||det!=0||!emptyModelTriangle(vertices,at))throw new IllegalArgumentException("Degenerate texture plane");
   // These exact projected positions have no filled-triangle coverage. Preserve
   // vertices/order and supply finite coefficients; all other singular cases reject.
   base[0]=vertices.get(at+2)/vertices.get(at+4);base[1]=vertices.get(at+3)/vertices.get(at+4);base[2]=1;
   if(!Float.isFinite(base[0])||!Float.isFinite(base[1]))throw new IllegalArgumentException("Texture plane overflow");
   return;
  }
  for(int c=0;c<3;c++){double a=vertices.get(at+2+c),b=vertices.get(at+7+c)-a,d=vertices.get(at+12+c)-a;base[c]=(float)(a/normal);dx[c]=(float)((b*cy-d*by)/(det*normal));dy[c]=(float)((bx*d-cx*b)/(det*normal));if(!Float.isFinite(base[c])||!Float.isFinite(dx[c])||!Float.isFinite(dy[c]))throw new IllegalArgumentException("Texture plane overflow");}
 }
 private static boolean emptyModelTriangle(FloatBuffer v,int at){
  for(int i=0;i<15;i++)if(!Float.isFinite(v.get(at+i)))return false;
  if(!(v.get(at+4)>0)||!(v.get(at+9)>0)||!(v.get(at+14)>0))return false;
  float ax=v.get(at),ay=v.get(at+1),bx=v.get(at+5),by=v.get(at+6),cx=v.get(at+10),cy=v.get(at+11);
  return (ax==bx&&bx==cx)||(ay==by&&by==cy)||(ax==bx&&ay==by)||(ax==cx&&ay==cy)||(bx==cx&&by==cy);
 }

}
