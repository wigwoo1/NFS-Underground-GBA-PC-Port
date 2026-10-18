package org.codex.nfsugpreview;
import java.nio.*;import java.nio.file.*;import java.security.*;import java.util.*;
public final class CombinedSnapshotTest {
 static int rejected=0,rows=0;static void check(boolean value){if(!value)throw new AssertionError();}
 static String hash(ByteBuffer b)throws Exception{MessageDigest d=MessageDigest.getInstance("SHA-256");d.update(b);StringBuilder s=new StringBuilder();for(byte v:d.digest())s.append(String.format("%02x",v&255));return s.toString();}
 static void reject(byte[] source,int offset,long value,boolean wide){byte[] copy=source.clone();ByteBuffer b=ByteBuffer.wrap(copy).order(ByteOrder.LITTLE_ENDIAN);if(wide)b.putLong(offset,value);else b.putInt(offset,(int)value);try{new NativeSceneSnapshot(copy);throw new AssertionError("Accepted mutation at "+offset);}catch(IllegalArgumentException expected){rejected++;}}
 public static void main(String[] args)throws Exception{
  for(int sample=0;sample<2;sample++){
   Path dir=Paths.get(args[0]);String name=sample==0?"whole":"split";byte[] input=Files.readAllBytes(dir.resolve(name+".nab"));NativeSceneSnapshot scene=new NativeSceneSnapshot(input);check(scene.kind==sample+1&&scene.geometryCount()==sample+1);
   List<String> expected=Files.readAllLines(dir.resolve(name+"-rows.txt"));check(expected.size()==160);
   for(int y=0;y<160;y++){check(hash(scene.row(y)).equals(expected.get(y)));rows++;}
   String digest=hash(scene.data());Arrays.fill(input,(byte)165);check(hash(scene.data()).equals(digest));
   ByteBuffer first=scene.data();first.position(3);check(scene.data().position()==0&&scene.packedLayers().position()==0&&scene.provenance().position()==0);
   try{scene.data().put(0,(byte)1);throw new AssertionError();}catch(ReadOnlyBufferException good){}
   try{scene.row(0).put(0,(byte)1);throw new AssertionError();}catch(ReadOnlyBufferException good){}
   try{scene.geometry(0).data().put(0,(byte)1);throw new AssertionError();}catch(ReadOnlyBufferException good){}
   try{scene.row(160);throw new AssertionError();}catch(IllegalArgumentException good){}
   byte[] source=Files.readAllBytes(dir.resolve(name+".nab"));ByteBuffer h=ByteBuffer.wrap(source).order(ByteOrder.LITTLE_ENDIAN);int geometry=(int)h.getLong(64),layer=(int)h.getLong(96),prov=(int)h.getLong(112);
   for(int offset:new int[]{0,8,16,24,32,40,56})reject(source,offset,offset==32?-1:0,true);
   reject(source,64,-1,true);reject(source,72,source.length,true);reject(source,80,0,true);reject(source,120,5311,true);
   reject(source,geometry,0,false);reject(source,geometry+4,99,false);reject(source,geometry+28,2,false);reject(source,geometry+32,99,false);
   for(int offset:new int[]{0,4,8,12,16,20,24,28})reject(source,layer+offset,offset==16?4001:0,false);
   reject(source,layer+32,0,false);reject(source,layer+36,1,false);byte[] badref=source.clone();badref[layer+20512]=(byte)255;badref[layer+20513]=(byte)255;try{new NativeSceneSnapshot(badref);throw new AssertionError();}catch(IllegalArgumentException good){rejected++;}
   for(int offset:new int[]{0,8,32,40,48,56})reject(source,prov+offset,0,true);
   reject(source,prov+24*8,0,true);reject(source,prov+27*8,0,true);
   int current=(int)h.getLong(56)==1?1:0; // locate packet identity in provenance, not assume an owner slot
   long serial=Integer.toUnsignedLong(h.getInt(geometry+16));for(int owner=0;owner<2;owner++)if(h.getLong(prov+(8+owner*8+1)*8)==serial)current=owner;
   reject(source,prov+(8+current*8+1)*8,0xffffffffL,true);
   if(sample==1)reject(source,48,h.getLong(48)+1,true);else reject(source,48,1,true);
   byte[] truncated=Arrays.copyOf(source,source.length-1);try{new NativeSceneSnapshot(truncated);throw new AssertionError();}catch(IllegalArgumentException good){rejected++;}
  }
  try{new NativeSceneSnapshot(null);throw new AssertionError();}catch(IllegalArgumentException good){rejected++;}
  System.out.println("PASS_COMBINED_SNAPSHOT_JAVA rows="+rows+" malformed="+rejected+" readonly=true owned=true");
 }
}
