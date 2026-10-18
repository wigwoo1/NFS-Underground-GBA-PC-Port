package org.codex.nfsugpreview;
import java.nio.*;
/** Sky-copy footprint only; caller must pair palettes with the displayed refresh. */
final class NativeSkyPlanes {
 final double weight;private final byte[][] rgba={new byte[153600],new byte[153600]};
 NativeSkyPlanes(NativeSky.Sample sample,byte[] palettes){if(sample==null||palettes==null||palettes.length!=81920)throw new IllegalArgumentException("sky palette rows");weight=sample.weight;ByteBuffer p=ByteBuffer.wrap(palettes).order(ByteOrder.LITTLE_ENDIAN);ByteBuffer[] indices={sample.lower(),sample.upper()};for(int side=0;side<2;side++)for(int i=0;i<15136;i++){int at=10560+i,index=indices[side].get(i)&255,color=p.getShort((at/240)*512+index*2)&65535;for(int c=0;c<3;c++){int v=(color>>(c*5))&31;rgba[side][at*4+c]=(byte)((v<<3)|(v>>2));}rgba[side][at*4+3]=(byte)255;}}
 private static ByteBuffer upload(byte[] data){ByteBuffer b=ByteBuffer.allocateDirect(data.length);b.put(data).flip();return b.asReadOnlyBuffer();}
 ByteBuffer lower(){return upload(rgba[0]);}ByteBuffer upper(){return upload(rgba[1]);}
}
