package org.codex.nfsugpreview;
import java.nio.*;import java.util.*;
/** Rebind source geometry inside validated original sky/background envelopes.
    Retained road/wall proof is still separate; this does not publish a live frame. */
final class NativeSourceBackgroundBinding {
 private static byte[] section(byte[] raw,int part){ByteBuffer b=ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN);int at=(int)b.getLong(64+part*16),bytes=(int)b.getLong(72+part*16);return Arrays.copyOfRange(raw,at,at+bytes);}
 private static byte[] replaceFirst(byte[] raw,byte[] first,int owners){byte[][] parts=new byte[owners+1][];parts[0]=first;long total=128+first.length;for(int i=1;i<parts.length;i++){parts[i]=section(raw,i);total+=parts[i].length;}if(total>66L*1024*1024)throw new IllegalArgumentException("Source background exceeds limit");ByteBuffer out=ByteBuffer.allocate((int)total).order(ByteOrder.LITTLE_ENDIAN);out.put(raw,0,128);out.putLong(16,total);int at=128;for(int i=0;i<parts.length;i++){out.putLong(64+i*16,at);out.putLong(72+i*16,parts[i].length);out.position(at);out.put(parts[i]);at+=parts[i].length;}return out.array();}
 /** Bytes and independently owned validated object for callers that need both. */
 static final class Bound {final byte[] bytes;final NativeBackgroundScene background;Bound(byte[] bytes){this.bytes=bytes;background=new NativeBackgroundScene(bytes);}}
 static byte[] bind(byte[] input,NativeSourceSceneBinding binding,NativeSourceSceneBinding.Source source){Bound result=bindPrepared(input,binding,source);return result==null?null:result.bytes;}
 static Bound bindPrepared(byte[] input,NativeSourceSceneBinding binding,NativeSourceSceneBinding.Source source){
  if(input==null)return null;if(binding==null||source==null)throw new IllegalArgumentException("Source provider required");byte[] owned=input.clone();NativeBackgroundScene original=new NativeBackgroundScene(owned);NativeSceneSnapshot scene=binding.bind(original.sky.scene,source);if(scene==null)return null;ByteBuffer data=scene.data();byte[] packet=new byte[data.remaining()];data.get(packet);int count=scene.geometryCount();byte[] sky=replaceFirst(section(owned,0),packet,count),result=replaceFirst(owned,sky,count);return new Bound(result);
 }
}
