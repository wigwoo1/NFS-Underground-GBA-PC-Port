package org.codex.nfsugpreview;
import java.nio.*;import java.nio.file.*;import java.util.*;
public final class SkySceneTest {
 static void ok(boolean b){if(!b)throw new AssertionError();}
 static void reject(byte[] b){try{new NativeSkyScene(b);throw new AssertionError("accepted malformed sky scene");}catch(IllegalArgumentException good){}}
 public static void main(String[] args)throws Exception{Path dir=Paths.get(args[0]);int covered=0,bad=0;for(String kind:new String[]{"whole","split"}){byte[] raw=Files.readAllBytes(dir.resolve("sky-scene-"+kind+".nsb")),expected=Files.readAllBytes(dir.resolve("sky-scene-"+kind+".rgba"));NativeSkyScene scene=new NativeSkyScene(raw);byte[] got=new byte[153600];ByteBuffer rgba=scene.exactRgba();ok(rgba.isReadOnly()&&rgba.isDirect());rgba.get(got);ok(Arrays.equals(got,expected));for(int i=3;i<got.length;i+=4)if(got[i]!=0)covered++;
 for(int at:new int[]{0,24,32,40,48,64,112}){byte[] invalid=raw.clone();invalid[at]^=1;reject(invalid);bad++;}ByteBuffer header=ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN);int sky=(int)header.getLong(80);byte[] invalid=raw.clone();invalid[sky+15192+header.getInt(sky+32)-header.getInt(sky+36)]^=1;reject(invalid);bad++;invalid=raw.clone();invalid[sky+8]^=1;reject(invalid);bad++;Arrays.fill(raw,(byte)0);byte[] retained=new byte[153600];scene.exactRgba().get(retained);ok(Arrays.equals(got,retained));}
 ok(covered==30272);System.out.println("PASS_SKY_SCENE_RGBA bytes=307200 covered="+covered+" malformed="+bad+" immutable=true");}
}
