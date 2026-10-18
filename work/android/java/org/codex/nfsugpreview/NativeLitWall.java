package org.codex.nfsugpreview;
import java.nio.*;
/** Validated original shading planes, with one bounded expanded upload variant. */
final class NativeLitWall {
 final NativeWallLighting curve;private final int pixels;
 private final ByteBuffer states,indices,light;private ByteBuffer cached;private int cachedLevel=-1;
 NativeLitWall(NativeScenePacket packet,NativeWorldScene world,int index,NativeWorldMesh mesh){
  NativeWorldScene.Surface s=world.surface(index);if(!s.lit||s.kind!=2||s.corners!=4||(s.mode!=3&&s.mode!=8)||s.planes!=17)throw new IllegalArgumentException("Explicit lit wall quad states required");
  curve=NativeWallLighting.surface(packet,world,index);if(curve==null&&mesh.triangleVertices!=0)throw new IllegalArgumentException("Unsupported lit wall edge visibility");
  pixels=s.width*s.height;states=s.states().asReadOnlyBuffer();ByteBuffer original=s.originalIndices();indices=original==null?null:original.asReadOnlyBuffer();light=s.lighting().asReadOnlyBuffer();
  // Validate every level before publication, even if it is never requested by a draw.
  for(int level=0;level<16;level++)for(int pixel=0;pixel<pixels;pixel++){int state=states.get((level+1)*pixels+pixel)&255;if(state>2)throw new IllegalArgumentException("Wall write state");if(indices!=null){int value=indices.get((level+1)*pixels+pixel)&255;if((state==2)!=(value!=0))throw new IllegalArgumentException("Wall mapped index state");}}
 }
 synchronized ByteBuffer variant(int level){if(level<0||level>=16)throw new IllegalArgumentException("Wall shade level");if(cachedLevel!=level){ByteBuffer out=ByteBuffer.allocateDirect(pixels*4);for(int pixel=0;pixel<pixels;pixel++){int state=states.get((level+1)*pixels+pixel)&255;if(indices!=null){out.put(indices.get((level+1)*pixels+pixel)).put((byte)0).put((byte)0);}else{int at=20+(level*pixels+pixel)*4;out.put(light.get(at)).put(light.get(at+1)).put(light.get(at+2));}out.put((byte)(state==0?0:state==1?128:255));}out.position(0);cached=out.asReadOnlyBuffer();cachedLevel=level;}return cached.asReadOnlyBuffer();}
}
