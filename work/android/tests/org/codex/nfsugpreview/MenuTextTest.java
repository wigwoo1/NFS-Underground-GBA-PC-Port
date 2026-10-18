package org.codex.nfsugpreview;
import java.nio.*;import java.nio.file.*;import java.util.*;
public final class MenuTextTest {
 static void check(boolean b){if(!b)throw new AssertionError();}
 static void reject(byte[] t,byte[] p){try{new NativeMenuText(t,p);throw new AssertionError("accepted malformed owner");}catch(IllegalArgumentException expected){}}
 public static void main(String[] args)throws Exception{
  Path dir=Paths.get(args[0]);byte[] t=Files.readAllBytes(dir.resolve("menu-4-positive.nft")),p=Files.readAllBytes(dir.resolve("menu-4-positive.nmp")),expected=Files.readAllBytes(dir.resolve("menu-text.rgba"));
  byte[] joined=Files.readAllBytes(dir.resolve("menu-4-positive.nmb"));byte[] joinedColor=new byte[153600];NativeMenuText.fromBundle(joined).rgba().get(joinedColor);check(Arrays.equals(joinedColor,expected));byte[] invalid=joined.clone();invalid[24]^=1;try{NativeMenuText.fromBundle(invalid);throw new AssertionError("bundle owner accepted");}catch(IllegalArgumentException good){}
  NativeMenuText text=new NativeMenuText(t,p);ByteBuffer b=text.rgba();check(b.isReadOnly()&&b.remaining()==153600);byte[] got=new byte[153600];b.get(got);check(Arrays.equals(got,expected));int covered=0;for(int i=3;i<got.length;i+=4)if(got[i]!=0)covered++;check(covered>0);
  byte[] bad=t.clone();bad[38480]=2;reject(bad,p);bad=p.clone();bad[24]^=1;reject(t,bad);bad=p.clone();bad[32]^=1;reject(t,bad);bad=t.clone();bad[64]=13;reject(bad,p);reject(Arrays.copyOf(t,t.length-1),p);
  Arrays.fill(t,(byte)0);Arrays.fill(p,(byte)0);byte[] again=new byte[153600];text.rgba().get(again);check(Arrays.equals(got,again));
  System.out.println("PASS_MENU_TEXT_RGBA_153600_BYTES covered="+covered+" malformed=5 immutable=true");
 }
}
