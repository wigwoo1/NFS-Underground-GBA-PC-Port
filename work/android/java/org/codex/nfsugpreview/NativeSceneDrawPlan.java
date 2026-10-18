package org.codex.nfsugpreview;
import java.nio.*;
/** Preflight all source-order commands before mutating a framebuffer. */
final class NativeSceneDrawPlan {
 static final class Draw {
  final NativeLitWall lighting;final NativeDrawBounds bounds;final boolean wall,model,indexed;final int index,width,height,vertices;
  private final FloatBuffer mesh;private final ByteBuffer image;
  Draw(boolean wall,boolean model,boolean indexed,int index,int w,int h,int n,FloatBuffer mesh,ByteBuffer image,NativeDrawBounds bounds,NativeLitWall lighting){this.lighting=lighting;this.bounds=bounds;this.wall=wall;this.model=model;this.indexed=indexed;this.index=index;width=w;height=h;vertices=n;this.mesh=mesh;ByteBuffer upload=ByteBuffer.allocateDirect(image.remaining());upload.put(image.duplicate()).position(0);this.image=upload.asReadOnlyBuffer();}
  FloatBuffer mesh(){return mesh.asReadOnlyBuffer();}ByteBuffer image(){return image.asReadOnlyBuffer();}
 }
 static ByteBuffer uploadImage(ByteBuffer rgba,ByteBuffer indices,ByteBuffer states){
  if(indices==null&&states==null)return rgba;int pixels=rgba.remaining()/4;ByteBuffer out=ByteBuffer.allocateDirect(pixels*4);
  if((indices!=null&&indices.remaining()!=pixels)||(states!=null&&states.remaining()!=pixels))throw new IllegalArgumentException("Unlit material plane size");
  for(int i=0;i<pixels;i++){
   if(indices!=null){out.put(indices.get(i)).put((byte)0).put((byte)0);}else{out.put(rgba.get(i*4)).put(rgba.get(i*4+1)).put(rgba.get(i*4+2));}
   int state=states==null?2:states.get(i)&255;if(state!=0&&state!=2)throw new IllegalArgumentException("Unlit wall state");out.put((byte)(state==0?0:255));
  }out.position(0);return out.asReadOnlyBuffer();
 }
 private final Draw[] draws;
 NativeSceneDrawPlan(NativeScenePacket packet){
  NativeWorldScene world=new NativeWorldScene(packet);

  draws=new Draw[world.commandCount()];
  for(int i=0;i<draws.length;i++){
   NativeWorldScene.Command c=world.command(i);NativeDrawBounds bounds=NativeDrawBounds.command(world.bounds(),world.surfaceCount(),c.model,c.index);
   if(c.model){NativeModelMesh m=new NativeModelMesh(NativeModelMesh.model(packet,c.index));
    ByteBuffer indices=m.originalIndices();
    draws[i]=new Draw(false,true,indices!=null,c.index,m.width,m.height,m.triangleVertices,m.vertices(),uploadImage(m.texture(),indices,null),bounds,null);
   }else{NativeWorldScene.Surface s=world.surface(c.index);
    if(s.lit?(s.mode!=3&&s.mode!=8):(s.mode!=0&&s.mode!=1&&s.mode!=2&&s.mode!=4&&s.mode!=5&&s.mode!=6&&s.mode!=7&&s.mode!=9&&s.mode!=10))throw new IllegalArgumentException("Unsupported lit/corrected world material");
    ByteBuffer image=s.texture();for(int t=3;t<image.remaining();t+=4){int a=image.get(t)&255;if(a!=0&&a!=255)throw new IllegalArgumentException("Legacy material alpha");}
    NativeWorldMesh m=new NativeWorldMesh(packet,world,c.index);NativeLitWall lighting=s.lit?new NativeLitWall(packet,world,c.index,m):null;
    draws[i]=new Draw(s.kind==2,false,s.originalIndices()!=null,c.index,s.width,s.height,m.triangleVertices,m.vertices(),lighting==null?uploadImage(image,s.originalIndices(),s.states()):lighting.variant(0),bounds,lighting);
   }
  }
 }
 int count(){return draws.length;}Draw draw(int i){return draws[i];}
}
