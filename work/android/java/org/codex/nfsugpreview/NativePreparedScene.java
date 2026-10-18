package org.codex.nfsugpreview;
import java.nio.ByteBuffer;
/** Validated CPU preparation retained with exactly one immutable source display. */
final class NativePreparedScene {
 final NativeBackgroundScene background;final NativeSceneSnapshot scene;
 final NativeSceneComposition composition;final NativeHudFrame hud;
 private final ByteBuffer rgba,palette;
 NativePreparedScene(NativeBackgroundScene background){if(background==null)throw new IllegalArgumentException("Source background required");this.background=background;scene=background.sky.scene;composition=new NativeSceneComposition(scene);hud=new NativeHudFrame(scene);rgba=background.exactRgba();palette=NativeHistoricalPalette.rgba(scene).asReadOnlyBuffer();}
 ByteBuffer backgroundRgba(){return rgba.asReadOnlyBuffer();}
 ByteBuffer paletteRgba(){return palette.asReadOnlyBuffer();}
}
