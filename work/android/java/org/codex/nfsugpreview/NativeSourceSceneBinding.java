package org.codex.nfsugpreview;
import java.nio.*;
/** Rebind owned source geometry to exact original display provenance. No GPU claim. */
final class NativeSourceSceneBinding {
 interface Source {byte[] packet(long epoch,long serial,long begin,long end);}
 private final NativeScenePacket[] cache=new NativeScenePacket[2];
 private static boolean same(NativeScenePacket a,NativeScenePacket b){return a!=null&&a.epoch==b.epoch&&a.serial==b.serial&&a.beginRefresh==b.beginRefresh&&a.endRefresh==b.endRefresh&&a.page==b.page;}
 void clear(){cache[0]=cache[1]=null;}
 NativeSceneSnapshot bind(NativeSceneSnapshot display,Source source){
  if(display==null||source==null)throw new IllegalArgumentException("Display and source are required");
  NativeScenePacket[] selected=new NativeScenePacket[display.geometryCount()];
  for(int i=0;i<selected.length;i++){
   NativeScenePacket owner=display.geometry(i);
   for(NativeScenePacket saved:cache)if(same(saved,owner)){selected[i]=saved;break;}
   if(selected[i]==null){byte[] raw=source.packet(owner.epoch,owner.serial,owner.beginRefresh,owner.endRefresh);if(raw==null)return null;NativeScenePacket packet=new NativeScenePacket(owner.epoch,raw);if(!same(packet,owner))throw new IllegalArgumentException("Source geometry owner mismatch");selected[i]=packet;}
  }
  ByteBuffer[] parts={selected[0].data(),selected.length==2?selected[1].data():ByteBuffer.allocate(0),display.packedLayers(),display.provenance()};
  long total=128;for(ByteBuffer part:parts)total+=part.remaining();if(total>64L*1024*1024)throw new IllegalArgumentException("Source display exceeds limit");
  ByteBuffer bytes=ByteBuffer.allocate((int)total).order(ByteOrder.LITTLE_ENDIAN);ByteBuffer header=display.data();header.limit(128);bytes.put(header);bytes.putLong(16,total);int at=128;
  for(int i=0;i<parts.length;i++){int size=parts[i].remaining();bytes.putLong(64+i*16,at);bytes.putLong(72+i*16,size);bytes.position(at);bytes.put(parts[i]);at+=size;}
  NativeSceneSnapshot result=new NativeSceneSnapshot(bytes.array());
  // Publish cache only after the entire whole/split join validates atomically.
  if(selected.length==2){cache[0]=selected[0];cache[1]=selected[1];}
  else if(!same(cache[0],selected[0])){cache[1]=cache[0];cache[0]=selected[0];}
  return result;
 }
}
