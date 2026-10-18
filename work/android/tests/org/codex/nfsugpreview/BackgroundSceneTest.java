package org.codex.nfsugpreview;
import java.nio.*;import java.nio.file.*;import java.util.*;
public class BackgroundSceneTest {
 public static void main(String[] args)throws Exception{
  int cells=0,rejected=0;
  for(String name:new String[]{"whole","split"}){
   Path dir=Paths.get(args[0]);byte[] raw=Files.readAllBytes(dir.resolve("race-background-"+name+".nrb"));NativeBackgroundScene s=new NativeBackgroundScene(raw);ByteBuffer rgba=s.exactRgba();byte[] actual=new byte[rgba.remaining()];rgba.get(actual);
   if(!Arrays.equals(actual,Files.readAllBytes(dir.resolve("background-"+name+".rgba"))))throw new AssertionError("Palette/coverage mismatch");
   raw[0]=0;if(!Arrays.equals(actual,bytes(s.exactRgba())))throw new AssertionError("Mutable input");
   byte[] valid=Files.readAllBytes(dir.resolve("race-background-"+name+".nrb"));ByteBuffer h=ByteBuffer.wrap(valid).order(ByteOrder.LITTLE_ENDIAN);int bg=(int)h.getLong(80);
   for(int offset:new int[]{0,8,16,24,32,56,64,112,bg+24,bg+32,bg+56,bg+64}){byte[] bad=valid.clone();bad[offset]^=64;try{new NativeBackgroundScene(bad);throw new AssertionError("Accepted mutation");}catch(IllegalArgumentException expected){rejected++;}}
   if(!s.exactRgba().isDirect()||!s.exactRgba().isReadOnly())throw new AssertionError("Buffer contract");cells+=38400;
  }System.out.println("PASS_BACKGROUND_SCENE cells="+cells+" rejected="+rejected);
 }
 static byte[] bytes(ByteBuffer b){byte[] r=new byte[b.remaining()];b.get(r);return r;}
}
