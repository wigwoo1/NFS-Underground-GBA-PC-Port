package org.codex.nfsugpreview;
import java.nio.*;import java.util.*;
/** Immutable displayed scene with exact sky owners/assets and historical palettes. */
final class NativeSkyScene {
 final NativeSceneSnapshot scene;private final NativeSky[] skies;private final byte[][] assets;private final byte[] palettes=new byte[81920];
 private static void require(boolean b){if(!b)throw new IllegalArgumentException("Invalid sky scene bundle");}
 NativeSkyScene(byte[] input){require(input!=null&&input.length>=128&&input.length<=65*1024*1024);ByteBuffer b=ByteBuffer.wrap(input).order(ByteOrder.LITTLE_ENDIAN);require(b.getLong(0)==0x3142534eL&&b.getLong(8)==1&&b.getLong(16)==input.length);long count=b.getLong(56);require(count==1||count==2);require(b.getLong(64)==128);long n=b.getLong(72);require(n>=128&&n<=input.length-128);scene=new NativeSceneSnapshot(Arrays.copyOfRange(input,128,128+(int)n));require(scene.epoch==b.getLong(24)&&scene.refresh==b.getLong(32)&&scene.kind==b.getLong(40)&&scene.splitRow==b.getLong(48)&&scene.geometryCount()==count);skies=new NativeSky[(int)count];assets=new byte[(int)count][];long end=128+n;
 for(int i=0;i<count;i++){long at=b.getLong(80+i*16),size=b.getLong(88+i*16);require(at==end&&size==30568&&size<=input.length-end);skies[i]=new NativeSky(Arrays.copyOfRange(input,(int)at,(int)at+15192));assets[i]=Arrays.copyOfRange(input,(int)at+15192,(int)at+30568);NativeScenePacket p=scene.geometry(i);NativeSky sky=skies[i];require(sky.epoch==scene.epoch&&sky.refresh>=p.beginRefresh&&sky.refresh<=p.endRefresh&&sky.destination==0x06002940L+p.page*0xa000L);sky.sample(sky,assets[i],0,0);end+=size;}
 require(end==input.length&&b.getLong(112)==0&&b.getLong(120)==0);if(count==1)require(b.getLong(96)==0&&b.getLong(104)==0);
 ByteBuffer layer=scene.packedLayers();for(int y=0;y<160;y++){int ref=layer.getShort(20512+(y*25+24)*2)&65535;ByteBuffer row=layer.duplicate();row.position(28512+ref*4096);row.get(palettes,y*512,512);}
 }
 NativeSky sky(int owner){return skies[owner];}
 ByteBuffer exactRgba(){ByteBuffer[] planes=new ByteBuffer[skies.length];for(int i=0;i<planes.length;i++)planes[i]=new NativeSkyPlanes(skies[i].sample(skies[i],assets[i],0,0),palettes).lower();ByteBuffer result=ByteBuffer.allocateDirect(153600);for(int y=0;y<160;y++){int owner=scene.kind==2&&y>=scene.splitRow?1:0;ByteBuffer row=planes[owner].duplicate();row.position(y*960);row.limit((y+1)*960);result.put(row);}result.flip();return result.asReadOnlyBuffer();}
}
