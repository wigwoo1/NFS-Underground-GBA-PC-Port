package org.codex.nfsugpreview;
/** Optional owned-text extension; all native calls remain on the core owner thread. */
final class NativeMenuCapture {
 static boolean enable(NativeCore core,boolean enabled){long h=core.ownerHandle();try{return enableNative(h,enabled);}catch(UnsatisfiedLinkError unavailable){return false;}}
 static byte[] capture(NativeCore core){long h=core.ownerHandle();try{return bundleNative(h);}catch(UnsatisfiedLinkError unavailable){return null;}}
 private static native boolean enableNative(long handle,boolean enabled);
 private static native byte[] bundleNative(long handle);
}
