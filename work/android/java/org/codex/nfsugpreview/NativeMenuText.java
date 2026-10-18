package org.codex.nfsugpreview;
import java.nio.*;
/** Immutable source-owned menu glyph colors; excludes other menu layers/effects. */
final class NativeMenuText {
 static NativeMenuText fromBundle(byte[] bundle){
  if(bundle==null||bundle.length!=158904)throw new IllegalArgumentException("menu bundle size");
  ByteBuffer b=ByteBuffer.wrap(bundle).order(ByteOrder.LITTLE_ENDIAN);
  if(b.getLong(0)!=0x31424d4eL||b.getLong(8)!=1||b.getLong(16)!=bundle.length||b.getLong(40)!=76880||b.getLong(48)!=81960||b.getLong(56)!=0)throw new IllegalArgumentException("menu bundle header");
  NativeMenuText text=new NativeMenuText(java.util.Arrays.copyOfRange(bundle,64,76944),java.util.Arrays.copyOfRange(bundle,76944,bundle.length));
  if(text.epoch!=b.getLong(24)||text.refresh!=b.getLong(32))throw new IllegalArgumentException("menu bundle owner");return text;
 }
 final long epoch,refresh; final int frontend; private final byte[] pixels;
 NativeMenuText(byte[] text,byte[] palette){
  if(text==null||palette==null||text.length!=76880||palette.length!=81960)throw new IllegalArgumentException("menu text size");
  ByteBuffer t=ByteBuffer.wrap(text).order(ByteOrder.LITTLE_ENDIAN),p=ByteBuffer.wrap(palette).order(ByteOrder.LITTLE_ENDIAN);
  if(t.getLong(0)!=0x31544d4eL||t.getLong(8)!=1||t.getLong(16)!=text.length||t.getLong(40)!=240||t.getLong(48)!=160||t.getLong(56)!=1||t.getLong(72)!=2)throw new IllegalArgumentException("menu text header");
  epoch=t.getLong(24);refresh=t.getLong(32);long f=t.getLong(64);
  if(epoch<=0||refresh<0||refresh>0xffffffffL||(f!=0&&f!=3&&f!=4&&f!=18))throw new IllegalArgumentException("menu context");frontend=(int)f;
  if(p.getLong(0)!=0x31504d4eL||p.getLong(8)!=1||p.getLong(16)!=palette.length||p.getLong(24)!=epoch||p.getLong(32)!=refresh)throw new IllegalArgumentException("palette owner");
  pixels=new byte[153600];
  for(int i=0;i<38400;i++){int coverage=text[38480+i]&255;if(coverage>1)throw new IllegalArgumentException("text coverage");if(coverage==0)continue;
   int index=text[80+i]&255,color=p.getShort(40+(i/240)*512+index*2)&65535;
   for(int c=0;c<3;c++){int v=(color>>(c*5))&31;pixels[i*4+c]=(byte)((v<<3)|(v>>2));}pixels[i*4+3]=(byte)255;
  }
 }
 ByteBuffer rgba(){ByteBuffer b=ByteBuffer.allocateDirect(pixels.length);b.put(pixels).flip();return b.asReadOnlyBuffer();}
}
