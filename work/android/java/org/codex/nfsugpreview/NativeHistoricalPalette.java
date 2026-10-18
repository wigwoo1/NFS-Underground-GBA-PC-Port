package org.codex.nfsugpreview;
import java.nio.*;
/** Display-owned BGR555 palette for each original scanline. */
final class NativeHistoricalPalette {
 static ByteBuffer rgba(NativeSceneSnapshot scene){ByteBuffer layer=scene.packedLayers(),out=ByteBuffer.allocateDirect(256*160*4);
  for(int y=0;y<160;y++){int ref=layer.getShort(20512+(y*25+24)*2)&65535;for(int index=0;index<256;index++){int color=layer.getShort(28512+ref*4096+index*2)&65535;for(int c=0;c<3;c++){int v=(color>>(c*5))&31;out.put((byte)((v<<3)|(v>>2)));}out.put((byte)255);}}
  out.position(0);return out.asReadOnlyBuffer();
 }
}
